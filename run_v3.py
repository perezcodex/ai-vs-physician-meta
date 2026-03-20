"""
v3 pipeline — expanded queries + Claude Sonnet screener.

Commands:
  python run_v3.py search
  python run_v3.py deduplicate
  python run_v3.py screen
  python run_v3.py extract
  python run_v3.py global_dedup
  python run_v3.py adjudication_queue
  python run_v3.py all

This workflow writes only to data_v3/.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from src.deduplicate import deduplicate

RAW_DIR = Path("data_v3/raw")
EXTRACTED_DIR = Path("data_v3/extracted")
LANES = [
    "diagnosis_reasoning_v3_core",
    "patient_facing_core",
    "admin_core",
    "supplemental_benchmark_implementation",
]


def cmd_search(args):
    from src.search_pubmed_v2 import search_pubmed_v2
    from src.search_medrxiv_v2 import search_medrxiv_v2
    from src.search_scopus_v2 import search_scopus_v2

    for lane in LANES:
        search_pubmed_v2(RAW_DIR / f"pubmed_{lane}.csv", force_refresh=args.force, lane=lane)
        search_medrxiv_v2(RAW_DIR / f"medrxiv_{lane}.csv", force_refresh=args.force, lane=lane)
        search_scopus_v2(
            RAW_DIR / f"scopus_{lane}.csv",
            force_refresh=args.force,
            import_csv=Path(args.scopus_csv) if args.scopus_csv else None,
            lane=lane,
        )


def cmd_deduplicate(args):
    for lane in LANES:
        deduplicate(
            raw_paths=[
                RAW_DIR / f"pubmed_{lane}.csv",
                RAW_DIR / f"medrxiv_{lane}.csv",
                RAW_DIR / f"scopus_{lane}.csv",
            ],
            out_path=RAW_DIR / f"combined_deduped_{lane}.csv",
        )


def cmd_screen(args):
    from src.screen_claude import screen_offline_v2

    for lane in LANES:
        lane_dir = EXTRACTED_DIR / lane
        screen_offline_v2(
            input_path=RAW_DIR / f"combined_deduped_{lane}.csv",
            out_path=lane_dir / "screened.csv",
            force_refresh=args.force,
            limit=args.limit,
        )


def cmd_extract(args):
    from src.extract_accuracy_offline_v2 import extract_accuracy_offline_v2

    for lane in LANES:
        lane_dir = EXTRACTED_DIR / lane
        extract_accuracy_offline_v2(
            input_path=lane_dir / "included.csv",
            out_path=lane_dir / "accuracy_candidates.csv",
            force_refresh=args.force,
            limit=args.limit,
        )


def cmd_global_dedup(args):
    from src.global_dedup import global_dedup

    lane_paths = [
        (lane, EXTRACTED_DIR / lane / "included.csv")
        for lane in LANES
    ]
    global_dedup(
        lane_included_paths=lane_paths,
        out_path=EXTRACTED_DIR / "included_global_deduped.csv",
        force_refresh=args.force,
    )


def cmd_adjudication_queue(args):
    from src.build_adjudication_queue_v3 import build_adjudication_queue

    build_adjudication_queue(EXTRACTED_DIR)


def cmd_all(args):
    cmd_search(args)
    cmd_deduplicate(args)
    cmd_screen(args)
    cmd_extract(args)
    cmd_global_dedup(args)
    cmd_adjudication_queue(args)


COMMANDS = {
    "search": cmd_search,
    "deduplicate": cmd_deduplicate,
    "screen": cmd_screen,
    "extract": cmd_extract,
    "global_dedup": cmd_global_dedup,
    "adjudication_queue": cmd_adjudication_queue,
    "all": cmd_all,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-vs-physician v3 pipeline")
    parser.add_argument("command", choices=COMMANDS.keys())
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--scopus-csv",
        default=None,
        help="Optional path to a manual Scopus CSV export. If omitted, the script expects SCOPUS_API_KEY.",
    )
    args = parser.parse_args()
    COMMANDS[args.command](args)
