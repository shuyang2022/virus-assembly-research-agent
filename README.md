# Virus Assembly Research Agent

A lightweight Flask web application that discovers recent virus assembly / capsid assembly papers from PubMed and presents them in a simple dashboard.

## Features
- Searches PubMed using NCBI E‑utilities with a set of predefined keywords.
- Rule‑based classification of papers (Experimental, Theoretical, Simulation, Other).
- Generates a short original summary from the title and abstract (no external LLMs).
- Dashboard shows paper cards with title, authors, date, source, category, summary and a link to PubMed.
- Refresh button to fetch the latest papers.
- Simple client‑side filters.

## Disclaimer
> **This tool displays public paper metadata and generated summaries for research discovery only. Please consult the original publications for full details.**

## Local Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

The app will be available at `http://127.0.0.1:5000`.

## Project Structure
```
virus-agent/
├─ app.py                     # Flask entry point
├─ search_agent.py            # PubMed fetcher
├─ classification_agent.py   # Rule‑based categoriser
├─ summary_agent.py           # Simple summary generator
├─ dashboard_agent.py         # Prepares data for the UI
├─ papers.json                # Cached results
├─ requirements.txt
├─ README.md
├─ .gitignore
├─ templates/
│   └─ index.html            # Dashboard HTML
└─ static/
    └─ style.css             # Styling
```
