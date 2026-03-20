"""
Europe PMC preprint search for the parallel v2 offline workflow.
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

from config.queries_v3 import DATE_END, DATE_START, MEDRXIV_LANE_QUERIES, QUERY_VERSION

BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
PAGE_SIZE = 200
_START = DATE_START.replace("/", "-")
_END = DATE_END.replace("/", "-")


def _build_query(lane_query: str) -> str:
    return f"({lane_query}) AND (SRC:PPR) AND (FIRST_PDATE:[{_START} TO {_END}])"


def _search_page(query: str, cursor_mark: str = "*") -> dict:
    params = {
        "query": query,
        "format": "json",
        "pageSize": PAGE_SIZE,
        "cursorMark": cursor_mark,
        "resultType": "core",
    }
    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def search_medrxiv_v2(out_path: Path, force_refresh: bool = False, lane: str = "clinical_core") -> pd.DataFrame:
    if out_path.exists() and not force_refresh:
        print(f"[medrxiv_v2] using cached {out_path}")
        return pd.read_csv(out_path)

    query = _build_query(MEDRXIV_LANE_QUERIES[lane])
    first = _search_page(query)
    total = int(first.get("hitCount", 0))
    print(f"[medrxiv_v2:{lane}] {total:,} total preprints")

    records = []
    cursor_mark = "*"
    with tqdm(total=total, desc=f"[medrxiv_v2:{lane}] fetching") as pbar:
        while True:
            page = _search_page(query, cursor_mark)
            results = page.get("resultList", {}).get("result", [])
            if not results:
                break

            for item in results:
                author_list = item.get("authorList", {}).get("author", [])
                authors = "; ".join(
                    f"{a.get('lastName', '')} {a.get('firstName', '')}".strip()
                    for a in author_list[:5]
                )
                if len(author_list) > 5:
                    authors += " et al."

                doi = (item.get("doi", "") or "").lower().strip()
                records.append(
                    {
                        "source": "medrxiv",
                        "source_id": item.get("id", doi),
                        "title": item.get("title", ""),
                        "abstract": item.get("abstractText", ""),
                        "authors": authors,
                        "journal": item.get("journalTitle", "Preprint"),
                        "year": str(item.get("firstPublicationDate", ""))[:4],
                        "doi": doi,
                        "query_version": QUERY_VERSION,
                    }
                )

            pbar.update(len(results))
            next_cursor = page.get("nextCursorMark")
            if not next_cursor or next_cursor == cursor_mark:
                break
            cursor_mark = next_cursor
            time.sleep(0.25)

    df = pd.DataFrame(records)
    if not df.empty:
        df["lane"] = lane
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"[medrxiv_v2:{lane}] saved {len(df):,} records → {out_path}")
    return df


if __name__ == "__main__":
    search_medrxiv_v2(Path("data_v2_offline/raw/medrxiv_raw.csv"), force_refresh=True)
