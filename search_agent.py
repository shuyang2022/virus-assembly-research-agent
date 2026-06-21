# search_agent.py
"""Search agent that queries PubMed (and optionally bioRxiv) for recent virus assembly papers.

It uses NCBI E-utilities (esearch + esummary + efetch) to retrieve metadata:
- PMID
- Title
- Authors (joined string)
- Publication date


Features:
- Fresh PubMed search on every refresh with primary and fallback keyword sets.
- Optional bioRxiv search (last 30 days) filtered by the same keywords.
- Random selection of a small set of recent papers (default 5).
- Prioritises papers from the last 12 months.
- Adds a `last_updated` timestamp (ISO 8601 UTC) to each record.
- Deduplicates results by DOI (or title when DOI missing).
- Logging of fetched and displayed counts.
"""

import json
import urllib.parse
import urllib.request
import random
import datetime
from typing import List, Dict, Set

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ESearch_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESummary_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
EFetch_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Primary PubMed search terms (combined with OR in the Title/Abstract field)
SEARCH_TERMS = [
    "virus assembly",
    "capsid assembly",
    "viral capsid",
    "virus self-assembly",
    "molecular dynamics viral capsid",
]

# Extra terms used when the primary query returns too few results
EXTRA_TERMS = [
    "viral capsid",
    "capsid assembly",
    "virus self-assembly",
    "virus morphogenesis",
    "molecular dynamics virus",
]

# How many candidate papers to fetch from each source
MAX_RESULTS = 30  # per source, enough for random sampling
# Minimum number of papers to display on the dashboard
MIN_DISPLAY = 5

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
def _http_get(url: str) -> bytes:
    """Perform a GET request and return the raw response bytes."""
    with urllib.request.urlopen(url, timeout=15) as response:
        return response.read()

def _now_iso() -> str:
    """Current UTC time in ISO‑8601 format with trailing 'Z'."""
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _build_query(terms: List[str]) -> str:
    """Create an OR query for PubMed Title/Abstract fields from a list of terms."""
    return " OR ".join(f'"{t}"[Title/Abstract]' for t in terms)

def _parse_pub_date(date_str: str) -> datetime.datetime:
    """Best‑effort conversion of PubMed date strings to ``datetime`` objects."""
    for fmt in ("%Y %b %d", "%Y %b", "%Y-%m-%d", "%Y"):
        try:
            return datetime.datetime.strptime(date_str, fmt)
        except Exception:
            continue
    return datetime.datetime.min

# ---------------------------------------------------------------------------
# PubMed pipeline
# ---------------------------------------------------------------------------
def _fetch_pubmed_ids(terms: List[str]) -> List[str]:
    query = _build_query(terms)
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
    if not pmid_list:
        return []
    ids = ",".join(pmid_list)
    params = {"db": "pubmed", "id": ids, "retmode": "json"}
    url = f"{ESummary_URL}?{urllib.parse.urlencode(params)}"
    data = json.loads(_http_get(url))
    result = []
    for uid in data.get("result", {}).get("uids", []):
        rec = data["result"][uid]
        title = rec.get("title", "")
        pubdate = rec.get("pubdate", "")
        authors = ", ".join(a.get("name", "") for a in rec.get("authors", []))
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
    params = {"db": "pubmed", "id": pmid, "rettype": "abstract", "retmode": "text"}
    url = f"{EFetch_URL}?{urllib.parse.urlencode(params)}"
    try:
        raw = _http_get(url).decode("utf-8", errors="ignore")
        return raw.strip()
    except Exception:
        return ""

def _search_pubmed() -> List[Dict]:
    """Run the PubMed search pipeline with fallback keywords if needed.
    Returns a list of paper dicts ready for the UI.
    """
    ids = _fetch_pubmed_ids(SEARCH_TERMS)
    summaries = _fetch_summary(ids)
    papers = []
    for s in summaries:
        papers.append({
            "title": s.get("title", ""),
            "abstract": _fetch_abstract(s["pmid"]),
            "authors": s.get("authors", ""),
            "pub_date": s.get("pub_date", ""),
            "doi": s.get("doi", ""),
            "url": s.get("url", ""),
            "source": "PubMed",
            "last_updated": _now_iso(),
        })
    if len(papers) < MIN_DISPLAY:
        combined_terms = list(set(SEARCH_TERMS + EXTRA_TERMS))
        ids = _fetch_pubmed_ids(combined_terms)
        summaries = _fetch_summary(ids)
        papers = []
        for s in summaries:
            papers.append({
                "title": s.get("title", ""),
                "abstract": _fetch_abstract(s["pmid"]),
                "authors": s.get("authors", ""),
                "pub_date": s.get("pub_date", ""),
                "doi": s.get("doi", ""),
                "url": s.get("url", ""),
                "source": "PubMed",
                "last_updated": _now_iso(),
            })
    print(f"[search_agent] PubMed fetched {len(papers)} candidates")
    return papers

# ---------------------------------------------------------------------------
# bioRxiv pipeline (optional)
# ---------------------------------------------------------------------------
def _search_biorxiv() -> List[Dict]:
    """Search the public bioRxiv API for recent pre‑prints matching our keywords.
    The API endpoint returns JSON for a date range: ``https://api.biorxiv.org/details/biorxiv/<from>/<to>``.
    We query the last 30 days, filter titles/abstracts for any of ``SEARCH_TERMS`` (case‑insensitive),
    and return a list of paper dicts with the same schema as PubMed.
    If the request fails, an empty list is returned so the app continues gracefully.
    """
    today = datetime.date.today()
    start = today - datetime.timedelta(days=30)
    url = f"https://api.biorxiv.org/details/biorxiv/{start.isoformat()}/{today.isoformat()}"
    try:
        raw = _http_get(url)
        data = json.loads(raw)
    except Exception as e:
        print(f"[search_agent] bioRxiv request error: {e}")
        return []
    records = data.get("collection", [])
    keywords = [kw.lower() for kw in SEARCH_TERMS]
    results: List[Dict] = []
    for rec in records:
        title = rec.get("title", "")
        abstract = rec.get("abstract", "")
        combined = f"{title} {abstract}".lower()
        if not any(kw in combined for kw in keywords):
            continue
        authors = rec.get("authors", "")
        doi = rec.get("doi", "")
        date = rec.get("date", "")
        url = rec.get("rel_link", "")
        results.append({
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "pub_date": date,
            "doi": doi,
            "url": url,
            "source": "bioRxiv",
            "last_updated": _now_iso(),
        })
    print(f"[search_agent] bioRxiv fetched {len(results)} candidates")
    return results

# ---------------------------------------------------------------------------
# Selection & deduplication utilities
# ---------------------------------------------------------------------------
def _deduplicate(papers: List[Dict]) -> List[Dict]:
    seen: Set[str] = set()
    unique: List[Dict] = []
    for p in papers:
        key = p.get("doi") or p.get("title")
        if not key:
            continue
        if key.lower() in seen:
            continue
        seen.add(key.lower())
        unique.append(p)
    return unique

def _select_display(papers: List[Dict]) -> List[Dict]:
    """Select up to ``MIN_DISPLAY`` items for the UI.
    - Sort newest first.
    - Prefer papers from the last 12 months when enough are available.
    - Randomly sample the final set.
    """
    if not papers:
        return []
    papers.sort(key=lambda p: _parse_pub_date(p.get("pub_date", "")), reverse=True)
    one_year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
    recent = [p for p in papers if _parse_pub_date(p.get("pub_date", "")) >= one_year_ago]
    pool = recent if len(recent) >= MIN_DISPLAY else papers
    if len(pool) <= MIN_DISPLAY:
        selected = pool
    else:
        selected = random.sample(pool, MIN_DISPLAY)
    print(f"[search_agent] Displaying {len(selected)} papers (from {len(papers)} candidates)")
    return selected

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def run() -> List[Dict]:
    """Entry point used by the Flask app.
    Combines PubMed and optional bioRxiv results, deduplicates, and selects a handful
    of recent papers for display.
    """
    pubmed = _search_pubmed()
    biorxiv = _search_biorxiv()
    combined = pubmed + biorxiv
    combined = _deduplicate(combined)
    display = _select_display(combined)
    return display
