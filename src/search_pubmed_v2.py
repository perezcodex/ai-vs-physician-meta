"""
PubMed search for the parallel v2 offline workflow.
"""
from __future__ import annotations

import json
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

from config.queries_v3 import DATE_END, DATE_START, PUBMED_LANE_QUERIES, QUERY_VERSION, pubmed_query

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
RETMAX = 500


def _esearch(query: str, retstart: int = 0) -> tuple[list[str], int]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": RETMAX,
        "retstart": retstart,
        "retmode": "json",
        "mindate": DATE_START,
        "maxdate": DATE_END,
        "datetype": "pdat",
    }
    for attempt in range(5):
        r = requests.post(f"{BASE_URL}/esearch.fcgi", data=params, timeout=30)
        r.raise_for_status()
        try:
            data = r.json()["esearchresult"]
            return data["idlist"], int(data["count"])
        except requests.exceptions.JSONDecodeError:
            try:
                cleaned = re.sub(r"[\x00-\x1f]+", " ", r.text)
                data = json.loads(cleaned)["esearchresult"]
                return data["idlist"], int(data["count"])
            except Exception:
                if attempt == 4:
                    raise
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("PubMed esearch failed after retries")


def _parse_pubmed_xml(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    records = []
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID", "")
        title_el = article.find(".//ArticleTitle")
        title = "".join(title_el.itertext()) if title_el is not None else ""
        abstract_parts = [
            "".join(node.itertext()) for node in article.findall(".//AbstractText")
        ]
        abstract = " ".join(part.strip() for part in abstract_parts if part.strip())

        authors = []
        for author in article.findall(".//Author"):
            last = author.findtext("LastName", "")
            first = author.findtext("ForeName", "")
            if last:
                authors.append(f"{last} {first}".strip())
        author_str = "; ".join(authors[:5]) + (" et al." if len(authors) > 5 else "")

        journal = article.findtext(".//Journal/Title", "")
        year = article.findtext(".//PubDate/Year", "")

        doi = ""
        for id_el in article.findall(".//ArticleId"):
            if id_el.get("IdType") == "doi":
                doi = (id_el.text or "").lower().strip()
                break

        records.append(
            {
                "source": "pubmed",
                "source_id": pmid,
                "title": title,
                "abstract": abstract,
                "authors": author_str,
                "journal": journal,
                "year": year,
                "doi": doi,
                "query_version": QUERY_VERSION,
            }
        )
    return records


def _efetch(pmids: list[str]) -> list[dict]:
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
    }
    r = requests.get(f"{BASE_URL}/efetch.fcgi", params=params, timeout=60)
    r.raise_for_status()
    return _parse_pubmed_xml(r.text)


def search_pubmed_v2(out_path: Path, force_refresh: bool = False, query: str | None = None, lane: str = "clinical_core") -> pd.DataFrame:
    if out_path.exists() and not force_refresh:
        print(f"[pubmed_v2] using cached {out_path}")
        return pd.read_csv(out_path)

    query = query or PUBMED_LANE_QUERIES.get(lane, pubmed_query())
    pmids, total = _esearch(query, retstart=0)
    print(f"[pubmed_v2:{lane}] {total:,} total records")

    all_pmids = list(pmids)
    for start in tqdm(range(RETMAX, total, RETMAX), desc=f"[pubmed_v2:{lane}] paging"):
        ids, _ = _esearch(query, retstart=start)
        all_pmids.extend(ids)
        time.sleep(0.34)

    all_pmids = list(dict.fromkeys(all_pmids))
    records = []
    batch_size = 200
    for i in tqdm(range(0, len(all_pmids), batch_size), desc=f"[pubmed_v2:{lane}] fetching"):
        records.extend(_efetch(all_pmids[i : i + batch_size]))
        time.sleep(0.34)

    df = pd.DataFrame(records)
    if not df.empty:
        df["lane"] = lane
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"[pubmed_v2:{lane}] saved {len(df):,} records → {out_path}")
    return df


if __name__ == "__main__":
    search_pubmed_v2(Path("data_v2_offline/raw/pubmed_raw.csv"), force_refresh=True)
