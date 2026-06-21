# search_agent.py
"""Search agent that queries PubMed (and optionally bioRxiv) for recent virus assembly papers.

It uses NCBI E-utilities (esearch + esummary + efetch) to retrieve metadata:
- PMID
- Title
- Authors (joined string)
- Publication date
- Abstract (if available)
- DOI (if present)
- URL to the PubMed entry

The `run` function returns a list of dictionaries with those fields.
If the PubMed request fails, it falls back to an empty list (the app will keep previous data).
A simple stub for bioRxiv is provided; it returns an empty list and can be expanded later.
"""

import json
import urllib.parse
import urllib.request
from typing import List, Dict

# Configuration
ESearch_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESummary_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
EFetch_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Search terms (OR combined)
SEARCH_TERMS = [
    "virus assembly",
    "capsid assembly",
    "viral capsid",
    "virus self-assembly",
    "molecular dynamics viral capsid",
]

# Maximum number of papers to fetch per refresh
MAX_RESULTS = 15


def _build_query() -> str:
    """Combine search terms into an OR query string for PubMed."""
    return " OR ".join(f'"{term}"[Title/Abstract]' for term in SEARCH_TERMS)


def _http_get(url: str) -> bytes:
    """Perform a GET request and return raw bytes. Raises on HTTP errors."""
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.read()


def _fetch_pubmed_ids() -> List[str]:
    """Return a list of PubMed IDs matching the query (up to MAX_RESULTS)."""
    query = _build_query()
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": str(MAX_RESULTS),
        "sort": "pub date",
    }
    url = f"{ESearch_URL}?{urllib.parse.urlencode(params)}"
    data = json.loads(_http_get(url))
    return data.get("esearchresult", {}).get("idlist", [])


def _fetch_summary(pmid_list: List[str]) -> List[Dict]:
    """Fetch summary information for a list of PMIDs.
    Returns a list of dicts with keys matching the desired output fields.
    """
    if not pmid_list:
        return []
    ids = ",".join(pmid_list)
    params = {
        "db": "pubmed",
        "id": ids,
        "retmode": "json",
    }
    url = f"{ESummary_URL}?{urllib.parse.urlencode(params)}"
    data = json.loads(_http_get(url))
    result = []
    uids = data.get("result", {}).get("uids", [])
    for uid in uids:
        rec = data["result"][uid]
        title = rec.get("title", "")
        pubdate = rec.get("pubdate", "")
        authors_list = rec.get("authors", [])
        authors = ", ".join(a.get("name", "") for a in authors_list)
        doi = ""
        for aid in rec.get("articleids", []):
            if aid.get("idtype") == "doi":
                doi = aid.get("value", "")
                break
        url = f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"
        result.append({
            "pmid": uid,
            "title": title,
            "authors": authors,
            "pub_date": pubdate,
            "doi": doi,
            "url": url,
        })
    return result


def _fetch_abstract(pmid: str) -> str:
    """Retrieve the abstract text for a single PMID using efetch.
    Returns an empty string if not available.
    """
    params = {
        "db": "pubmed",
        "id": pmid,
        "rettype": "abstract",
        "retmode": "text",
    }
    url = f"{EFetch_URL}?{urllib.parse.urlencode(params)}"
    try:
        raw = _http_get(url).decode("utf-8", errors="ignore")
        return raw.strip()
    except Exception:
        return ""


def _search_pubmed() -> List[Dict]:
    """Main PubMed search pipeline – returns list of paper dicts.
    Each dict contains: title, abstract, authors, pub_date, url, doi.
    """
    try:
        ids = _fetch_pubmed_ids()
        summaries = _fetch_summary(ids)
        papers = []
        for summary in summaries:
            abstract = _fetch_abstract(summary["pmid"])
            paper = {
                "title": summary.get("title", ""),
                "abstract": abstract,
                "authors": summary.get("authors", ""),
                "pub_date": summary.get("pub_date", ""),
                "doi": summary.get("doi", ""),
                "url": summary.get("url", ""),
                "source": "PubMed",
            }
            papers.append(paper)
        return papers
    except Exception as e:
        print(f"[search_agent] PubMed fetch error: {e}")
        return []


def _search_biorxiv() -> List[Dict]:
    """Optional bioRxiv search – currently returns an empty list.
    The function can be expanded later; it fails gracefully.
    """
    return []


def run() -> List[Dict]:
    """Public entry point used by the Flask app.
    Combines PubMed (primary) and bioRxiv (optional) results.
    """
    papers = _search_pubmed()
    # papers.extend(_search_biorxiv())  # Uncomment to include bioRxiv results when implemented
    return papers
