"""
Rule-based screener for the parallel v2 offline workflow.

This is intentionally conservative. It generates:
- include
- exclude
- uncertain

The goal is to expand the corpus without paying for Anthropic while preserving a
reviewable audit trail.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from config.queries_v2_offline import AI_TERMS, CLINICAL_TASK_TERMS, EXCLUSION_CRITERIA, PHYSICIAN_TERMS # Took a look at these files, comments will be in there

# Overall agree with the exclusions here.
# Some board/licensing exams are used to later evaluate residents. 
# Are those excluded under this context?

EXCLUDE_PATTERNS = [
    "systematic review",
    "meta-analysis",
    "review article",
    "editorial",
    "commentary",
    "letter to the editor",
    "protocol",
    "study protocol",
    "medical student",
    "usmle",
    "board exam",
    "multiple-choice",
]

# I think this covers a good range from CNN to LLM, one thing I would add
# is signal processing, things like sensor data, this is currently more a 
# field for consumer health products, however there is research like TRICORDER 
# leveraging signal processing to detect heart disease.

GENERIC_AI_PATTERNS = [
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "neural network",
    "predictive model",
    "decision support system",
    "clinical decision support",
    "natural language processing",
    "computer vision",
    "large language model",
    "generative ai",

     # proposed additions for signal processing studies
    "signal processing",
    "digital signal processing",
]

# Agree with overall accuracy patterns, include top-K studies and percentage (0-100) studies.
# Are accuracy patterns required? What would happen if didn't constrain pull by fields?

# If we do any statistical calculations, which accuracy patterns to include may be
# constratined by those requirements (ex: calculating effect size, weighting, heterogeniety)

ACCURACY_PATTERNS = [
    r"\baccuracy\b",
    r"\bauc\b",
    r"\bauroc\b",
    r"\bsensitivity\b",
    r"\bspecificity\b",
    r"\bf1\b",
    r"\bprecision\b",
    r"\brecall\b",
    r"\b\d{1,3}(?:\.\d+)?%\b",

    # proposed scalable regex addition for Top-K studies
    r"\btop[- ]?\d+(?:\s+accuracy)?\b",
    r"\btop[- ]?k(?:\s+accuracy)?\b",
]

STRONG_COMPARISON_PATTERNS = [
    "compared",
    "comparison",
    "versus",
    "vs.",
    "vs ",
    "against",
    "outperformed",
    "inferior to",
    "superior to",
    "randomized",
    "trial",
    "reader study",
]

ASSISTED_COMPARISON_PATTERNS = [
    "assisted",
    "unassisted",
    "with ai",
    "without ai",
    "doctor+ai",
    "physician-only",
    "ai-only",
    "human-ai collaboration",
]


def _contains_any(text: str, terms: list[str]) -> bool:
    text = text.lower()
    return any(term.lower() in text for term in terms)


def _accuracy_signal(text: str) -> bool:
    text = text.lower()
    return any(re.search(pattern, text) for pattern in ACCURACY_PATTERNS)


def _screen_row(row: dict) -> dict:
    title = str(row.get("title", "") or "")
    abstract = str(row.get("abstract", "") or "")
    text = f"{title}\n{abstract}".lower()

    has_ai = _contains_any(text, AI_TERMS) or _contains_any(text, GENERIC_AI_PATTERNS)
    has_task = _contains_any(text, CLINICAL_TASK_TERMS)
    has_physician = _contains_any(text, PHYSICIAN_TERMS)
    has_exclusion = any(pattern in text for pattern in EXCLUDE_PATTERNS)
    has_accuracy = _accuracy_signal(text)
    has_strong_comparison = any(phrase in text for phrase in STRONG_COMPARISON_PATTERNS)
    has_assisted_comparison = any(phrase in text for phrase in ASSISTED_COMPARISON_PATTERNS)
    has_performance_language = any(
        phrase in text
        for phrase in [
            "physician performance",
            "human performance",
            "clinician performance",
            "compared with",
            "compared to",
            "relative to",
        ]
    )
    has_comparison = has_physician and (has_strong_comparison or has_assisted_comparison or has_performance_language)
    strong_include = has_ai and has_task and has_physician and (has_strong_comparison or has_assisted_comparison)
    weak_but_possible = has_ai and has_task and (has_physician or has_performance_language or has_accuracy)

    if has_exclusion:
        decision = "exclude"
        reason = "Matched exclusion-pattern language in title/abstract."
    elif strong_include:
        decision = "include"
        reason = "Contains AI, healthcare task, and explicit human-comparison signals."
    elif weak_but_possible:
        decision = "uncertain"
        reason = "Contains AI/task/human signals but comparison is weak or only partially explicit."
    else:
        decision = "exclude"
        reason = "Missing required AI, clinician, or clinical-task signals."

    return {
        **row,
        "screen_decision": decision,
        "screen_reason": reason,
        "screen_has_physician_comparison": bool(has_comparison),
        "screen_has_physician_condition": bool(
            any(term in text for term in ["conventional", "resources", "workup", "unaided", "assisted", "ehr"])
        ),
        "screen_has_accuracy_metric": bool(has_accuracy),
        "screen_notes": "",
    }


def screen_offline_v2(
    input_path: Path,
    out_path: Path,
    force_refresh: bool = False,
    limit: int | None = None,
) -> pd.DataFrame:
    if out_path.exists() and not force_refresh:
        print(f"[screen_offline_v2] using cached {out_path}")
        return pd.read_csv(out_path)

    df = pd.read_csv(input_path)
    if limit:
        df = df.head(limit)

    results = pd.DataFrame([_screen_row(row) for row in df.to_dict("records")])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(out_path, index=False)

    included_path = out_path.parent / "included.csv"
    uncertain_path = out_path.parent / "uncertain.csv"
    results[results["screen_decision"] == "include"].to_csv(included_path, index=False)
    results[results["screen_decision"] == "uncertain"].to_csv(uncertain_path, index=False)

    print(f"[screen_offline_v2] include={len(results[results['screen_decision'] == 'include']):,}")
    print(f"[screen_offline_v2] uncertain={len(results[results['screen_decision'] == 'uncertain']):,}")
    print(f"[screen_offline_v2] exclude={len(results[results['screen_decision'] == 'exclude']):,}")
    return results


if __name__ == "__main__":
    screen_offline_v2(
        input_path=Path("data_v2_offline/raw/combined_deduped.csv"),
        out_path=Path("data_v2_offline/extracted/screened.csv"),
        force_refresh=True,
    )
