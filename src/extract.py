"""
Claude full-text extractor.

For each study in included.csv, Claude reads the full text (if accessible via
DOI → Unpaywall → PDF text) or falls back to the abstract, and extracts
structured comparison arm data.

Outputs:
  data/extracted/extracted_arms.csv   — one row per comparison arm per study
  data/extracted/needs_manual.csv     — studies Claude couldn't extract confidently
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import anthropic
import pandas as pd
import requests
from tqdm import tqdm

MODEL       = "claude-sonnet-4-6"
TEMPERATURE = 0

# ── Unpaywall: finds legal open-access PDF URLs ───────────────────────────────
UNPAYWALL_EMAIL = "your-email@example.com"   # required by Unpaywall ToS


def _get_oa_pdf_url(doi: str) -> str | None:
    """Return open-access PDF URL via Unpaywall, or None if paywalled."""
    if not doi:
        return None
    try:
        r = requests.get(
            f"https://api.unpaywall.org/v2/{doi}",
            params={"email": UNPAYWALL_EMAIL},
            timeout=10,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        best = data.get("best_oa_location")
        if best:
            return best.get("url_for_pdf") or best.get("url")
    except Exception:
        pass
    return None


def _fetch_pdf_text(pdf_url: str) -> str:
    """Download PDF and extract text (basic — first 8,000 chars)."""
    try:
        import io
        import pdfminer.high_level as pdfminer
        r = requests.get(pdf_url, timeout=30)
        r.raise_for_status()
        text = pdfminer.extract_text(io.BytesIO(r.content))
        return (text or "")[:8000]
    except Exception:
        return ""


SYSTEM_PROMPT = """\
You are a data extractor for a systematic review meta-analysis comparing
AI diagnostic performance to physicians.
Extract structured data from the provided study text.
Respond ONLY with valid JSON — no prose, no markdown.
"""

EXTRACT_PROMPT = """\
Extract all physician-comparison arms from this study.

STUDY TEXT:
{text}

For each comparison arm, extract:
- arm_type: one of
    AI_vs_physician_unaided          (AI vs physician with no tools/vignette)
    AI_vs_physician_resources        (AI vs physician with conventional clinical tools)
    AI_plus_physician_vs_physician_unaided      (AI+physician team vs unaided physician)
    AI_plus_physician_vs_physician_resources    (AI+physician team vs physician with tools)
    AI_vs_AI_plus_physician          (AI alone vs AI+physician team)
- physician_condition: unaided | conventional_resources | ai_assisted | unknown
- physician_type: expert | non_expert | mixed | unknown
- physician_specialty: string (e.g. "radiologist", "emergency physician", "general physician")
- ai_model: string (e.g. "GPT-4", "Claude 3 Opus")
- accuracy_ai: float or null (proportion, 0-1 scale — convert % to decimal)
- accuracy_physician: float or null
- metric: accuracy | AUC | sensitivity | specificity | F1 | other
- n_cases: integer or null
- p_value: float or null (for AI vs physician difference)
- ai_better: true | false | null (null if no significant difference reported)
- specialty: string
- tier: I | II | III | unknown
    Tier I = real-world patient data (prospective study, retrospective EHR/cohort, RCT with real patients)
    Tier II = real clinical cases in a structured/controlled evaluation (e.g. standardised case sets, reader studies with real patient images)
    Tier III = exam questions, medical board questions, USMLE, clinical vignettes — no real patients
- physician_condition_detail: free text describing exactly what resources physician had
- confidence: 0.0-1.0 (your confidence in this extraction)
- notes: any important caveats

Return:
{{
  "study_title": "string",
  "first_author": "string",
  "year": integer or null,
  "arms": [ {{ ...arm fields above... }}, ... ],
  "has_conventional_resources_arm": true | false,
  "has_ai_plus_physician_arm": true | false,
  "overall_notes": "string"
}}

If no physician comparison arm exists, return {{"arms": [], "overall_notes": "no physician comparison found"}}.
"""


def extract(
    input_path: Path,
    out_path: Path,
    force_refresh: bool = False,
) -> pd.DataFrame:
    if out_path.exists() and not force_refresh:
        print(f"[extract] using cached {out_path}")
        return pd.read_csv(out_path)

    df = pd.read_csv(input_path)
    print(f"[extract] extracting from {len(df):,} included studies...")

    client = anthropic.Anthropic()
    arm_rows   = []
    needs_manual = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="[extract]"):
        doi      = str(row.get("doi", "") or "")
        title    = str(row.get("title", "") or "")
        abstract = str(row.get("abstract", "") or "")
        source   = str(row.get("source", "") or "")
        source_id = str(row.get("source_id", "") or "")

        # Try to get full text
        full_text = ""
        pdf_url = _get_oa_pdf_url(doi)
        if pdf_url:
            full_text = _fetch_pdf_text(pdf_url)

        text = full_text if len(full_text) > 500 else f"TITLE: {title}\n\nABSTRACT: {abstract}"
        text_source = "full_text" if len(full_text) > 500 else "abstract_only"

        for attempt in range(3):
            try:
                msg = client.messages.create(
                    model=MODEL,
                    max_tokens=2000,
                    temperature=TEMPERATURE,
                    system=SYSTEM_PROMPT,
                    messages=[{
                        "role": "user",
                        "content": EXTRACT_PROMPT.format(text=text),
                    }],
                )
                raw = msg.content[0].text.strip()
                parsed = json.loads(raw)
                break
            except (json.JSONDecodeError, anthropic.APIError) as e:
                if attempt == 2:
                    parsed = {"arms": [], "overall_notes": f"extraction error: {e}"}
                time.sleep(2 ** attempt)

        arms = parsed.get("arms", [])
        if not arms:
            needs_manual.append({
                "source": source,
                "source_id": source_id,
                "doi": doi,
                "title": title,
                "text_source": text_source,
                "overall_notes": parsed.get("overall_notes", ""),
            })
            continue

        for arm in arms:
            confidence = float(arm.get("confidence", 0))
            arm_rows.append({
                "source":        source,
                "source_id":     source_id,
                "doi":           doi,
                "title":         parsed.get("study_title", title),
                "first_author":  parsed.get("first_author", ""),
                "year":          parsed.get("year", row.get("year")),
                "text_source":   text_source,
                **{k: arm.get(k) for k in [
                    "arm_type", "physician_condition", "physician_type",
                    "physician_specialty", "ai_model",
                    "accuracy_ai", "accuracy_physician", "metric",
                    "n_cases", "p_value", "ai_better", "specialty",
                    "tier", "physician_condition_detail",
                    "confidence", "notes",
                ]},
                "needs_review": confidence < 0.7,
            })

    arms_df = pd.DataFrame(arm_rows)
    manual_df = pd.DataFrame(needs_manual)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    arms_df.to_csv(out_path, index=False)

    manual_path = out_path.parent / "needs_manual.csv"
    manual_df.to_csv(manual_path, index=False)

    print(f"\n[extract] {len(arms_df):,} comparison arms extracted")
    print(f"  needs manual review: {len(manual_df):,} studies + {(arms_df['needs_review']).sum():,} low-confidence arms")
    print(f"  arms by type:\n{arms_df['arm_type'].value_counts().to_string()}")
    print(f"  physician condition:\n{arms_df['physician_condition'].value_counts().to_string()}")
    print(f"  extracted → {out_path}")
    print(f"  manual    → {manual_path}")

    return arms_df


if __name__ == "__main__":
    extract(
        input_path=Path("data/extracted/included.csv"),
        out_path=Path("data/extracted/extracted_arms.csv"),
        force_refresh=True,
    )
