"""
Scopus search support for the parallel v2 offline workflow.

This script supports two paths:
1. Elsevier Scopus Search API, if SCOPUS_API_KEY is available.
2. CSV import from a manual Scopus export.

That keeps the workflow usable without adding a paid API dependency to the
original project.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from tqdm import tqdm

from config.queries_v3 import QUERY_VERSION, SCOPUS_LANE_QUERIES

load_dotenv()

BASE_URL = "https://api.elsevier.com/content/search/scopus"
COUNT = 25


def _normalize_csv(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "Title": "title",
        "title": "title",
        "Abstract": "abstract",
        "abstract": "abstract",
        "Authors": "authors",
        "authors": "authors",
        "Source title": "journal",
        "journal": "journal",
        "Year": "year",
        "year": "year",
        "DOI": "doi",
        "doi": "doi",
        "EID": "source_id",
        "eid": "source_id",
    }
    for old, new in rename_map.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})

    for col in ["title", "abstract", "authors", "journal", "year", "doi", "source_id"]:
        if col not in df.columns:
            df[col] = ""

    return pd.DataFrame(
        {
            "source": "scopus",
            "source_id": df["source_id"].fillna("").astype(str),
            "title": df["title"].fillna("").astype(str),
            "abstract": df["abstract"].fillna("").astype(str),
            "authors": df["authors"].fillna("").astype(str),
            "journal": df["journal"].fillna("").astype(str),
            "year": df["year"].fillna("").astype(str),
            "doi": df["doi"].fillna("").astype(str).str.lower().str.strip(),
            "query_version": QUERY_VERSION,
        }
    )


def import_scopus_csv(csv_path: Path, out_path: Path, lane: str = "clinical_core") -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    normalized = _normalize_csv(df)
    normalized["lane"] = lane
    out_path.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(out_path, index=False)
    print(f"[scopus_v2] imported {len(normalized):,} rows from {csv_path} → {out_path}")
    return normalized


def search_scopus_v2(
    out_path: Path,
    force_refresh: bool = False,
    import_csv: Path | None = None,
    lane: str = "clinical_core",
) -> pd.DataFrame:
    if out_path.exists() and not force_refresh:
        print(f"[scopus_v2] using cached {out_path}")
        return pd.read_csv(out_path)

    if import_csv:
        return import_scopus_csv(import_csv, out_path, lane=lane)

    api_key = os.getenv("SCOPUS_API_KEY")
    insttoken = os.getenv("SCOPUS_INSTTOKEN")
    if not api_key:
        raise RuntimeError(
            "SCOPUS_API_KEY not set. Either provide Scopus credentials or use "
            "--scopus-csv with a manual Scopus export."
        )

    headers = {"X-ELS-APIKey": api_key, "Accept": "application/json"}
    if insttoken:
        headers["X-ELS-Insttoken"] = insttoken

    start = 0
    total = None
    records: list[dict] = []

    query = SCOPUS_LANE_QUERIES[lane]
    while total is None or start < total:
        params = {"query": query, "start": start, "count": COUNT}
        r = requests.get(BASE_URL, headers=headers, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()["search-results"]
        if total is None:
            total = int(data.get("opensearch:totalResults", 0))
            print(f"[scopus_v2:{lane}] {total:,} total results")

        entries = data.get("entry", [])
        if not entries:
            break

        for item in entries:
            records.append(
                {
                    "source": "scopus",
                    "source_id": item.get("eid", ""),
                    "title": item.get("dc:title", ""),
                    "abstract": item.get("dc:description", ""),
                    "authors": item.get("dc:creator", ""),
                    "journal": item.get("prism:publicationName", ""),
                    "year": item.get("prism:coverDate", "")[:4],
                    "doi": (item.get("prism:doi", "") or "").lower().strip(),
                    "query_version": QUERY_VERSION,
                }
            )

        start += COUNT
        tqdm.write(f"[scopus_v2:{lane}] fetched {min(start, total):,}/{total:,}")
        time.sleep(0.5)

    df = pd.DataFrame(records)
    if not df.empty:
        df["lane"] = lane
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"[scopus_v2:{lane}] saved {len(df):,} records → {out_path}")
    return df


if __name__ == "__main__":
    search_scopus_v2(Path("data_v2_offline/raw/scopus_raw.csv"), force_refresh=True)
