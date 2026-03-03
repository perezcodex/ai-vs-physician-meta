"""
Claude abstract screener.

For each record in combined_deduped.csv, Claude decides:
  include / exclude / uncertain

Outputs:
  data/extracted/screened.csv   — all records with screening decision
  data/extracted/included.csv   — records to proceed to full-text review
  data/extracted/uncertain.csv  — records for human review
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import anthropic
import pandas as pd
from tqdm import tqdm

from config.queries import INCLUSION_CRITERIA, EXCLUSION_CRITERIA

MODEL   = "claude-haiku-4-5-20251001"
TEMPERATURE = 0

SYSTEM_PROMPT = """\
You are a systematic review screener for a meta-analysis.
Your task: given a study title and abstract, decide whether the study meets inclusion criteria.
Respond ONLY with valid JSON — no prose, no markdown.
"""

def _build_prompt(title: str, abstract: str) -> str:
    inclusion = "\n".join(f"- {c}" for c in INCLUSION_CRITERIA)
    exclusion = "\n".join(f"- {c}" for c in EXCLUSION_CRITERIA)
    return f"""
TITLE: {title}

ABSTRACT: {abstract or "(no abstract available)"}

INCLUSION CRITERIA (ALL must be met):
{inclusion}

EXCLUSION CRITERIA (ANY triggers exclusion):
{exclusion}

Respond with JSON:
{{
  "decision": "include" | "exclude" | "uncertain",
  "reason": "one-sentence explanation",
  "has_physician_comparison": true | false,
  "has_physician_condition_detail": true | false,
  "notes": "any relevant detail about physician condition or AI+physician arm"
}}

has_physician_condition_detail = true if the abstract explicitly states what resources
the physician had (e.g. EHR access, standard clinical tools, conventional workup, references).
"""


def screen(
    input_path: Path,
    out_path: Path,
    force_refresh: bool = False,
) -> pd.DataFrame:
    if out_path.exists() and not force_refresh:
        print(f"[screen] using cached {out_path}")
        return pd.read_csv(out_path)

    df = pd.read_csv(input_path)
    print(f"[screen] screening {len(df):,} records with {MODEL}...")

    client = anthropic.Anthropic()
    results = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="[screen]"):
        title    = str(row.get("title", ""))
        abstract = str(row.get("abstract", ""))

        for attempt in range(3):
            try:
                msg = client.messages.create(
                    model=MODEL,
                    max_tokens=300,
                    temperature=TEMPERATURE,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": _build_prompt(title, abstract)}],
                )
                raw = msg.content[0].text.strip()
                parsed = json.loads(raw)
                break
            except (json.JSONDecodeError, anthropic.APIError) as e:
                if attempt == 2:
                    parsed = {
                        "decision": "uncertain",
                        "reason": f"parsing error: {e}",
                        "has_physician_comparison": False,
                        "has_physician_condition_detail": False,
                        "notes": "",
                    }
                time.sleep(2 ** attempt)

        results.append({
            **row.to_dict(),
            "screen_decision":                    parsed.get("decision", "uncertain"),
            "screen_reason":                      parsed.get("reason", ""),
            "screen_has_physician_comparison":    parsed.get("has_physician_comparison", False),
            "screen_has_physician_condition":     parsed.get("has_physician_condition_detail", False),
            "screen_notes":                       parsed.get("notes", ""),
        })

    result_df = pd.DataFrame(results)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(out_path, index=False)

    counts = result_df["screen_decision"].value_counts()
    print(f"\n[screen] results:")
    print(f"  include:   {counts.get('include', 0):,}")
    print(f"  exclude:   {counts.get('exclude', 0):,}")
    print(f"  uncertain: {counts.get('uncertain', 0):,}")

    # Write split files
    included_path = out_path.parent / "included.csv"
    uncertain_path = out_path.parent / "uncertain.csv"
    result_df[result_df["screen_decision"] == "include"].to_csv(included_path, index=False)
    result_df[result_df["screen_decision"] == "uncertain"].to_csv(uncertain_path, index=False)
    print(f"  included  → {included_path}")
    print(f"  uncertain → {uncertain_path}  ← human review needed")

    return result_df


if __name__ == "__main__":
    screen(
        input_path=Path("data/raw/combined_deduped.csv"),
        out_path=Path("data/extracted/screened.csv"),
        force_refresh=True,
    )
