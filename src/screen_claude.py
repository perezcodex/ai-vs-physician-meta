"""
LLM-based screener for the parallel v2 offline workflow.

Uses claude-sonnet-4-6 to classify papers as include / exclude / uncertain.
Preserves the same CSV input/output interface as the rule-based v2 screener.
Uses the Batches API for 50% cost savings on large runs.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

import anthropic
import pandas as pd
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are screening abstracts for a systematic review with two research questions:
1. Does AI perform better than physicians on clinical tasks?
2. When AI assists physicians, do physician+AI combinations outperform AI alone?

Classify each paper as exactly one of:
- include: The study directly addresses either research question with measurable outcomes. This includes:
  (a) AI vs physician/clinician head-to-head comparison
  (b) Physician+AI vs AI alone comparison
  (c) Three-arm studies with AI, physician, and physician+AI conditions
- uncertain: Partial signals of AI-physician comparison, indirect comparison, or unclear study design
- exclude: No AI-physician or AI-augmentation comparison, or matches an exclusion criterion

Always exclude if any of the following apply:
- Systematic review, meta-analysis, review article, editorial, commentary, letter to the editor
- Study protocol or pre-registration
- Compares AI only to medical students, board exams, or multiple-choice benchmarks with no physician arm

For each paper also identify which study arms are present based on what the abstract describes.

Respond with a JSON object only — no markdown, no explanation outside the JSON:
{
  "screen_decision": "include" | "exclude" | "uncertain",
  "screen_reason": "<1-2 sentences citing specific signals in the text>",
  "screen_has_physician_comparison": true | false,
  "screen_has_physician_condition": true | false,
  "screen_has_accuracy_metric": true | false,
  "arm_ai_alone": true | false,
  "arm_physician_alone": true | false,
  "arm_physician_plus_ai": true | false,
  "screen_notes": "<any caveats, or empty string>"
}"""


def _parse_result(result) -> dict:
    fallback = {
        "screen_decision": "uncertain",
        "screen_reason": "Failed to parse model response.",
        "screen_has_physician_comparison": False,
        "screen_has_physician_condition": False,
        "screen_has_accuracy_metric": False,
        "arm_ai_alone": False,
        "arm_physician_alone": False,
        "arm_physician_plus_ai": False,
        "screen_notes": "parse_error",
    }
    if result is None or result.result.type != "succeeded":
        return fallback
    try:
        text = next(b.text for b in result.result.message.content if b.type == "text")
        parsed = json.loads(text)
        return {
            "screen_decision": parsed.get("screen_decision", "uncertain"),
            "screen_reason": parsed.get("screen_reason", ""),
            "screen_has_physician_comparison": bool(parsed.get("screen_has_physician_comparison", False)),
            "screen_has_physician_condition": bool(parsed.get("screen_has_physician_condition", False)),
            "screen_has_accuracy_metric": bool(parsed.get("screen_has_accuracy_metric", False)),
            "arm_ai_alone": bool(parsed.get("arm_ai_alone", False)),
            "arm_physician_alone": bool(parsed.get("arm_physician_alone", False)),
            "arm_physician_plus_ai": bool(parsed.get("arm_physician_plus_ai", False)),
            "screen_notes": parsed.get("screen_notes", ""),
        }
    except Exception as e:
        fallback["screen_notes"] = f"parse_error: {e}"
        return fallback


def screen_offline_v2(
    input_path: Path,
    out_path: Path,
    force_refresh: bool = False,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    if out_path.exists() and not force_refresh:
        print(f"[screen_offline_v2] using cached {out_path}")
        return pd.read_csv(out_path)

    df = pd.read_csv(input_path)
    if limit:
        df = df.head(limit)
    records = df.to_dict("records")

    client = anthropic.Anthropic()

    requests = [
        Request(
            custom_id=str(i),
            params=MessageCreateParamsNonStreaming(
                model=MODEL,
                max_tokens=640,
                system=SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Title: {str(row.get('title', '') or '')}\n\n"
                        f"Abstract: {str(row.get('abstract', '') or '')}"
                    ),
                }],
            ),
        )
        for i, row in enumerate(records)
    ]

    print(f"[screen_offline_v2] submitting batch ({len(requests):,} papers) ...")
    batch = client.messages.batches.create(requests=requests)
    print(f"[screen_offline_v2] batch_id={batch.id}")

    while True:
        batch = client.messages.batches.retrieve(batch.id)
        c = batch.request_counts
        print(
            f"[screen_offline_v2] {batch.processing_status} — "
            f"processing={c.processing} succeeded={c.succeeded} errored={c.errored}"
        )
        if batch.processing_status == "ended":
            break
        time.sleep(30)

    result_map = {r.custom_id: r for r in client.messages.batches.results(batch.id)}

    screened = []
    for i, row in enumerate(records):
        decision = _parse_result(result_map.get(str(i)))
        screened.append({**row, **decision})

    results = pd.DataFrame(screened)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(out_path, index=False)

    included = results[results["screen_decision"] == "include"]
    uncertain = results[results["screen_decision"] == "uncertain"]
    included.to_csv(out_path.parent / "included.csv", index=False)
    uncertain.to_csv(out_path.parent / "uncertain.csv", index=False)

    print(f"[screen_offline_v2] include={len(included):,}")
    print(f"[screen_offline_v2] uncertain={len(uncertain):,}")
    print(f"[screen_offline_v2] exclude={len(results) - len(included) - len(uncertain):,}")
    return results


if __name__ == "__main__":
    screen_offline_v2(
        input_path=Path("data_v2_offline/raw/combined_deduped.csv"),
        out_path=Path("data_v2_offline/extracted/screened.csv"),
        force_refresh=True,
    )
