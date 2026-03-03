"""
Merge records from PubMed, medRxiv, and arXiv and deduplicate.
Dedup strategy (in order):
  1. Exact DOI match (lowercased, stripped)
  2. Normalised title + year match (lowercase, strip punctuation)
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


def _normalize_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def deduplicate(raw_paths: list[Path], out_path: Path) -> pd.DataFrame:
    frames = []
    for p in raw_paths:
        if p.exists():
            df = pd.read_csv(p)
            frames.append(df)
            print(f"  loaded {len(df):,} records from {p.name}")
        else:
            print(f"  [skip] {p} not found")

    if not frames:
        raise FileNotFoundError("No raw search files found — run search first.")

    combined = pd.concat(frames, ignore_index=True)
    print(f"\n  combined: {len(combined):,} records")

    # ── Step 1: dedup on DOI ──────────────────────────────────────────────────
    has_doi  = combined[combined["doi"].notna() & (combined["doi"] != "")]
    no_doi   = combined[combined["doi"].isna()  | (combined["doi"] == "")]

    # Prefer pubmed > medrxiv > arxiv when DOIs clash
    source_rank = {"pubmed": 0, "medrxiv": 1, "arxiv": 2}
    has_doi = has_doi.copy()
    has_doi["_rank"] = has_doi["source"].map(source_rank).fillna(9)
    has_doi = has_doi.sort_values("_rank").drop_duplicates(subset="doi", keep="first")
    has_doi = has_doi.drop(columns="_rank")

    # ── Step 2: dedup remaining by normalised title + year ───────────────────
    no_doi = no_doi.copy()
    no_doi["_norm_title"] = no_doi["title"].fillna("").apply(_normalize_title)

    has_doi["_norm_title"] = has_doi["title"].fillna("").apply(_normalize_title)

    all_norm_titles = set(has_doi["_norm_title"])
    no_doi = no_doi[~no_doi["_norm_title"].isin(all_norm_titles)]
    no_doi = no_doi.drop_duplicates(subset=["_norm_title", "year"], keep="first")

    deduped = pd.concat([has_doi, no_doi], ignore_index=True).drop(columns="_norm_title")

    print(f"  after dedup: {len(deduped):,} unique records")
    print(f"  by source:   {deduped['source'].value_counts().to_dict()}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    deduped.to_csv(out_path, index=False)
    print(f"  saved → {out_path}")
    return deduped


if __name__ == "__main__":
    deduplicate(
        raw_paths=[
            Path("data/raw/pubmed_raw.csv"),
            Path("data/raw/medrxiv_raw.csv"),
            Path("data/raw/arxiv_raw.csv"),
        ],
        out_path=Path("data/raw/combined_deduped.csv"),
    )
