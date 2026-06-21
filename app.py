# app.py
"""Main Flask application for Virus Assembly Research Agent MVP.
Provides three routes:
- '/' renders the UI.
- '/api/papers' returns stored paper metadata as JSON.
- '/refresh' triggers fetching from PubMed, classification, summarization, and stores results in papers.json.
"""

from flask import Flask, render_template, jsonify
import os, json
from datetime import datetime

# Import agents (they reside in the same directory)
from search_agent import run as search_papers
from classification_agent import classify
from summary_agent import summarize

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "papers.json")

def load_papers():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_papers(papers):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/papers')
def api_papers():
    return jsonify(load_papers())

@app.route('/refresh', methods=['POST'])
def refresh():
    # Perform fresh search and log counts
    raw = search_papers()
    print(f"[app] Fetched {len(raw)} papers from search agents")
    processed = []
    for rec in raw:
        abstract = rec.get('abstract', '')
        category = classify(abstract)
        summary = summarize(abstract)
        processed.append({
            'title': rec.get('title', ''),
            'authors': rec.get('authors', ''),
            'pub_date': rec.get('pub_date', ''),
            'category': category,
            'summary': summary,
            'url': rec.get('url', ''),
            'source': rec.get('source', ''),
            'last_updated': rec.get('last_updated', ''),
        })
    print(f"[app] Processed and will display {len(processed)} papers")
    # Save processed papers (which already include source and last_updated)
    save_papers(processed)
    # Return status with count and timestamp
    return jsonify({"status": "updated", "count": len(processed), "last_updated": datetime.utcnow().replace(microsecond=0).isoformat() + "Z"})

if __name__ == '__main__':
    app.run(debug=True)
