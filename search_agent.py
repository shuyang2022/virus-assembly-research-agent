# search_agent.py
"""Simple PubMed search stub for virus assembly papers.
Returns a list of dictionaries with keys: title, abstract, authors, pub_date, url.
In a real implementation, this would query NCBI Entrez E-utilities.
"""
import random

def _static_papers():
    # A small static dataset for demonstration purposes.
    return [
        {
            "title": "Structural insights into virus capsid assembly",
            "abstract": "We report cryo‑EM structures of capsid intermediates revealing mechanisms of assembly. Experimental data show...",
            "authors": "Doe J, Smith A",
            "pub_date": "2024-05-10",
            "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
        },
        {
            "title": "Computational modeling of viral capsid formation",
            "abstract": "Using coarse‑grained simulations we investigate the kinetic pathways of capsid assembly. Theoretical analysis suggests...",
            "authors": "Lee K, Patel R",
            "pub_date": "2023-11-22",
            "url": "https://pubmed.ncbi.nlm.nih.gov/87654321/",
        },
        {
            "title": "Experimental validation of capsid protein interactions",
            "abstract": "Biochemical assays confirm the role of specific residues in capsid protein‑protein interactions. Experimental results...",
            "authors": "Nguyen L, Chen Y",
            "pub_date": "2025-01-15",
            "url": "https://pubmed.ncbi.nlm.nih.gov/11223344/",
        },
    ]

def run():
    """Return a list of paper records.
    In a production system this would perform a network request; here we return static data.
    """
    papers = _static_papers()
    random.shuffle(papers)
    return papers
