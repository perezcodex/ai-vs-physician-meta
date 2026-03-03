"""
CLI for the AI-vs-physician meta-analysis pipeline.

Commands:
  python run.py search       — run all three searches (PubMed, medRxiv, arXiv)
  python run.py deduplicate  — merge + deduplicate search results
  python run.py screen       — Claude abstract screening
  python run.py extract      — Claude full-text extraction
  python run.py all          — run full pipeline end to end
"""
from __future__ import annotations

import argparse
from pathlib import Path

RAW_DIR       = Path("data/raw")
EXTRACTED_DIR = Path("data/extracted")


def cmd_search(args):
    from src.search_pubmed   import search_pubmed
    from src.search_medrxiv  import search_medrxiv
    from src.search_arxiv    import search_arxiv

    force = args.force
    search_pubmed( RAW_DIR / "pubmed_raw.csv",  force_refresh=force)
    search_medrxiv(RAW_DIR / "medrxiv_raw.csv", force_refresh=force)
    search_arxiv(  RAW_DIR / "arxiv_raw.csv",   force_refresh=force)


def cmd_deduplicate(args):
    from src.deduplicate import deduplicate
    deduplicate(
        raw_paths=[
            RAW_DIR / "pubmed_raw.csv",
            RAW_DIR / "medrxiv_raw.csv",
            RAW_DIR / "arxiv_raw.csv",
        ],
        out_path=RAW_DIR / "combined_deduped.csv",
    )


def cmd_screen(args):
    from src.screen import screen
    screen(
        input_path=RAW_DIR / "combined_deduped.csv",
        out_path=EXTRACTED_DIR / "screened.csv",
        force_refresh=args.force,
    )


def cmd_extract(args):
    from src.extract import extract
    extract(
        input_path=EXTRACTED_DIR / "included.csv",
        out_path=EXTRACTED_DIR / "extracted_arms.csv",
        force_refresh=args.force,
    )


def cmd_all(args):
    args.force = getattr(args, "force", False)
    cmd_search(args)
    cmd_deduplicate(args)
    cmd_screen(args)
    cmd_extract(args)


COMMANDS = {
    "search":      cmd_search,
    "deduplicate": cmd_deduplicate,
    "screen":      cmd_screen,
    "extract":     cmd_extract,
    "all":         cmd_all,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-vs-physician meta-analysis pipeline")
    parser.add_argument("command", choices=COMMANDS.keys())
    parser.add_argument("--force", action="store_true",
                        help="bypass cache and re-run even if output exists")
    args = parser.parse_args()
    COMMANDS[args.command](args)
