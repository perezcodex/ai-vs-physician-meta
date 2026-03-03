"""
PubMed E-utilities search for AI-vs-physician studies.
Saves raw records to data/raw/pubmed_raw.csv
"""
from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

from config.queries import pubmed_query, DATE_START, DATE_END, QUERY_VERSION

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
RETMAX   = 500   # records per page (PubMed max = 10,000 but 500 is safe)


def _esearch(query: str, retstart: int = 0) -> tuple[list[str], int]:
    """Return (list_of_pmids, total_count)."""
    params = {
        "db":       "pubmed",
        "term":     query,
        "retmax":   RETMAX,
        "retstart": retstart,
        "retmode":  "json",
        "mindate":  DATE_START,
        "maxdate":  DATE_END,
        "datetype": "pdat",
    }
    r = requests.get(f"{BASE_URL}/esearch.fcgi", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()["esearchresult"]
    return data["idlist"], int(data["count"])


def _efetch(pmids: list[str]) -> list[dict]:
    """Fetch abstract records for a list of PMIDs."""
    params = {
        "db":      "pubmed",
        "id":      ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
    }
    r = requests.get(f"{BASE_URL}/efetch.fcgi", params=params, timeout=60)
    r.raise_for_status()
    return _parse_pubmed_xml(r.text)


def _parse_pubmed_xml(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    records = []
    for article in root.findall(".//PubmedArticle"):
        pmid_el = article.find(".//PMID")
        pmid = pmid_el.text if pmid_el is not None else ""

        title_el = article.find(".//ArticleTitle")
        title = "".join(title_el.itertext()) if title_el is not None else ""

        abstract_el = article.find(".//AbstractText")
        abstract = "".join(abstract_el.itertext()) if abstract_el is not None else ""

        # Authors
        authors = []
        for author in article.findall(".//Author"):
            last  = author.findtext("LastName", "")
            first = author.findtext("ForeName", "")
            if last:
                authors.append(f"{last} {first}".strip())
        author_str = "; ".join(authors[:5]) + (" et al." if len(authors) > 5 else "")

        # Journal + year
        journal = article.findtext(".//Journal/Title", "")
        year_el = article.find(".//PubDate/Year")
        year = year_el.text if year_el is not None else ""

        # DOI
        doi = ""
        for id_el in article.findall(".//ArticleId"):
            if id_el.get("IdType") == "doi":
                doi = id_el.text or ""
                break

        records.append({
            "source":     "pubmed",
            "source_id":  pmid,
            "title":      title,
            "abstract":   abstract,
            "authors":    author_str,
            "journal":    journal,
            "year":       year,
            "doi":        doi.lower().strip(),
            "query_version": QUERY_VERSION,
        })
    return records


def search_pubmed(out_path: Path, force_refresh: bool = False) -> pd.DataFrame:
    if out_path.exists() and not force_refresh:
        print(f"[pubmed] using cached {out_path}")
        return pd.read_csv(out_path)

    query = pubmed_query()
    print(f"[pubmed] query: {query[:120]}...")

    # First call to get total count
    pmids, total = _esearch(query, retstart=0)
    print(f"[pubmed] {total:,} total records")

    all_pmids = list(pmids)
    for start in tqdm(range(RETMAX, total, RETMAX), desc="[pubmed] paging"):
        ids, _ = _esearch(query, retstart=start)
        all_pmids.extend(ids)
        time.sleep(0.34)  # respect 3 req/s limit

    # Deduplicate PMIDs
    all_pmids = list(dict.fromkeys(all_pmids))
    print(f"[pubmed] fetching {len(all_pmids):,} records...")

    records = []
    batch_size = 200
    for i in tqdm(range(0, len(all_pmids), batch_size), desc="[pubmed] fetching"):
        batch = all_pmids[i : i + batch_size]
        records.extend(_efetch(batch))
        time.sleep(0.34)

    df = pd.DataFrame(records)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"[pubmed] saved {len(df):,} records → {out_path}")
    return df


if __name__ == "__main__":
    search_pubmed(Path("data/raw/pubmed_raw.csv"), force_refresh=True)
