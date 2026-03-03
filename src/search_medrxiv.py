"""
Europe PMC search for AI-vs-physician preprints (medRxiv + bioRxiv + others).

Europe PMC indexes preprints with keyword search — far more efficient than
paging through all medRxiv records.

API docs: https://europepmc.org/RestfulWebService
Saves raw records to data/raw/medrxiv_raw.csv
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

from config.queries import MEDRXIV_QUERY, DATE_START, DATE_END, QUERY_VERSION

BASE_URL  = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
PAGE_SIZE = 200   # Europe PMC max per page

# Europe PMC date format: YYYY-MM-DD
_START = DATE_START.replace("/", "-")
_END   = DATE_END.replace("/", "-")


def _build_query() -> str:
    """Construct Europe PMC query: keyword + preprint filter + date range."""
    return (
        f"({MEDRXIV_QUERY})"
        f" AND (SRC:PPR)"            # PPR = preprint source
        f" AND (FIRST_PDATE:[{_START} TO {_END}])"
    )


def _search_page(query: str, cursor_mark: str = "*") -> dict:
    params = {
        "query":      query,
        "format":     "json",
        "pageSize":   PAGE_SIZE,
        "cursorMark": cursor_mark,
        "resultType": "core",        # includes abstract
    }
    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def search_medrxiv(out_path: Path, force_refresh: bool = False) -> pd.DataFrame:
    if out_path.exists() and not force_refresh:
        print(f"[europepmc] using cached {out_path}")
        return pd.read_csv(out_path)

    query = _build_query()
    print(f"[europepmc] query: {query[:120]}...")

    # First page to get hit count
    first = _search_page(query)
    total = int(first.get("hitCount", 0))
    print(f"[europepmc] {total:,} total preprints")

    records = []
    cursor_mark = "*"

    with tqdm(total=total, desc="[europepmc] fetching") as pbar:
        while True:
            page = _search_page(query, cursor_mark)
            results = page.get("resultList", {}).get("result", [])
            if not results:
                break

            for item in results:
                # Europe PMC author string
                author_list = item.get("authorList", {}).get("author", [])
                authors = "; ".join(
                    f"{a.get('lastName', '')} {a.get('firstName', '')}".strip()
                    for a in author_list[:5]
                )
                if len(author_list) > 5:
                    authors += " et al."

                doi = (item.get("doi", "") or "").lower().strip()
                records.append({
                    "source":        "medrxiv",
                    "source_id":     item.get("id", doi),
                    "title":         item.get("title", ""),
                    "abstract":      item.get("abstractText", ""),
                    "authors":       authors,
                    "journal":       item.get("journalTitle", "Preprint"),
                    "year":          str(item.get("firstPublicationDate", ""))[:4],
                    "doi":           doi,
                    "query_version": QUERY_VERSION,
                })

            pbar.update(len(results))

            next_cursor = page.get("nextCursorMark")
            if not next_cursor or next_cursor == cursor_mark:
                break
            cursor_mark = next_cursor
            time.sleep(0.25)   # Europe PMC rate limit: ~10 req/s is safe

    df = pd.DataFrame(records)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"[europepmc] saved {len(df):,} records → {out_path}")
    return df


if __name__ == "__main__":
    search_medrxiv(Path("data/raw/medrxiv_raw.csv"), force_refresh=True)
