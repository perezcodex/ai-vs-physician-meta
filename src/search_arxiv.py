"""
arXiv Atom API search for AI-vs-physician studies.
Saves raw records to data/raw/arxiv_raw.csv
"""
from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

from config.queries import ARXIV_QUERY, DATE_START, DATE_END, QUERY_VERSION

BASE_URL   = "https://export.arxiv.org/api/query"
PAGE_SIZE  = 200
NS         = {"atom": "http://www.w3.org/2005/Atom"}

# arXiv date filter uses submittedDate in YYYYMMDDTTTT format
_START_DT = DATE_START.replace("/", "") + "0000"
_END_DT   = DATE_END.replace("/", "") + "2359"


def _fetch_page(start: int) -> tuple[list[dict], int]:
    params = {
        "search_query": (
            f"all:{ARXIV_QUERY} "
            f"AND submittedDate:[{_START_DT} TO {_END_DT}]"
        ),
        "start":      start,
        "max_results": PAGE_SIZE,
        "sortBy":     "submittedDate",
        "sortOrder":  "descending",
    }
    r = requests.get(BASE_URL, params=params, timeout=60)
    r.raise_for_status()

    root  = ET.fromstring(r.text)
    total_el = root.find("opensearch:totalResults",
                         {"opensearch": "http://a9.com/-/spec/opensearch/1.1/"})
    total = int(total_el.text) if total_el is not None else 0

    records = []
    for entry in root.findall("atom:entry", NS):
        title    = (entry.findtext("atom:title", "", NS) or "").strip().replace("\n", " ")
        abstract = (entry.findtext("atom:summary", "", NS) or "").strip().replace("\n", " ")

        # Quick relevance filter
        text = (title + " " + abstract).lower()
        ai_hit = any(t in text for t in ["large language model", "llm", "gpt", "generative ai",
                                          "claude", "gemini", "llama", "mistral"])
        ph_hit = any(t in text for t in ["physician", "clinician", "doctor", "radiologist",
                                          "human performance", "human-ai"])
        if not (ai_hit and ph_hit):
            continue

        arxiv_id = ""
        id_el = entry.find("atom:id", NS)
        if id_el is not None:
            arxiv_id = id_el.text.split("/abs/")[-1] if "/abs/" in (id_el.text or "") else ""

        doi = ""
        for link in entry.findall("atom:link", NS):
            if link.get("title") == "doi":
                doi = link.get("href", "").replace("https://doi.org/", "").lower().strip()

        authors = []
        for author in entry.findall("atom:author", NS):
            name = author.findtext("atom:name", "", NS)
            if name:
                authors.append(name)
        author_str = "; ".join(authors[:5]) + (" et al." if len(authors) > 5 else "")

        published = entry.findtext("atom:published", "", NS)[:10]
        year = published[:4]

        records.append({
            "source":        "arxiv",
            "source_id":     arxiv_id,
            "title":         title,
            "abstract":      abstract,
            "authors":       author_str,
            "journal":       "arXiv",
            "year":          year,
            "doi":           doi,
            "query_version": QUERY_VERSION,
        })

    return records, total


def search_arxiv(out_path: Path, force_refresh: bool = False) -> pd.DataFrame:
    if out_path.exists() and not force_refresh:
        print(f"[arxiv] using cached {out_path}")
        return pd.read_csv(out_path)

    print(f"[arxiv] query: {ARXIV_QUERY[:80]}...")

    first_records, total = _fetch_page(0)
    print(f"[arxiv] {total:,} total results")

    all_records = list(first_records)
    for start in tqdm(range(PAGE_SIZE, min(total, 5000), PAGE_SIZE), desc="[arxiv] paging"):
        records, _ = _fetch_page(start)
        all_records.extend(records)
        time.sleep(3)  # arXiv rate limit: be polite

    df = pd.DataFrame(all_records)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"[arxiv] saved {len(df):,} relevant records → {out_path}")
    return df


if __name__ == "__main__":
    search_arxiv(Path("data/raw/arxiv_raw.csv"), force_refresh=True)
