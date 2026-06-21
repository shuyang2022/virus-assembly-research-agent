# summary_agent.py
"""Very simple summarizer that returns a short excerpt of the abstract.
In a real system this could call an LLM; here we truncate to the first 200 characters.
"""

def summarize(abstract: str) -> str:
    """Return a short summary of the abstract.
    If abstract is longer than 200 characters, truncate and add ellipsis.
    """
    if not abstract:
        return ""
    return (abstract[:200] + "..." ) if len(abstract) > 200 else abstract
