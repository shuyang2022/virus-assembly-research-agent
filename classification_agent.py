# classification_agent.py
"""Simple rule‑based classifier for virus assembly papers.

The `classify` function examines the abstract text and returns one of:
- "Experimental"
- "Theoretical"
- "Simulation"
- "Other"
"""

import re

def classify(abstract: str) -> str:
    """Return a category based on simple keyword matching.
    """
    if not abstract:
        return "Other"
    text = abstract.lower()
    experimental_keywords = ["experiment", "experimental", "biochemical", "assay", "in vitro", "lab", "wet lab"]
    theoretical_keywords = ["theory", "theoretical", "analytical", "model", "framework"]
    simulation_keywords = ["simulation", "simulations", "simulated", "computational", "coarse‑grained", "molecular dynamics"]
    if any(kw in text for kw in experimental_keywords):
        return "Experimental"
    if any(kw in text for kw in simulation_keywords):
        return "Simulation"
    if any(kw in text for kw in theoretical_keywords):
        return "Theoretical"
    return "Other"
