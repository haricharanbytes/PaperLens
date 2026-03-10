"""
app/app.py
Flask entry point — serves the frontend and exposes API routes
that call the existing Python pipeline modules.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from fetcher.arxiv_fetcher   import fetch_by_id, fetch_by_title, detect_input_type, extract_id_from_url
from utils.helpers            import prepare_paper
from summarizer.summarize     import summarize_paper
from explainer.concept_explainer import explain_paper_concepts

load_dotenv()

app = Flask(__name__)


# ── Pages ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/app")
def summarizer():
    return render_template("summarizer.html")


# ── API Routes ────────────────────────────────────────────────────────────────

@app.route("/api/fetch", methods=["POST"])
def api_fetch():
    """
    Detect input type and fetch paper metadata from ArXiv.
    Body: { "query": "2303.08774" | "https://arxiv.org/..." | "attention is all you need" }
    """
    data  = request.get_json()
    query = (data or {}).get("query", "").strip()
    if not query:
        return jsonify({"error": "query is required"}), 400

    try:
        kind = detect_input_type(query)

        if kind == "url":
            paper_id = extract_id_from_url(query)
            paper    = fetch_by_id(paper_id)
            return jsonify({"type": "single", "paper": paper})

        elif kind == "id":
            clean = query.lower().replace("arxiv:", "")
            paper = fetch_by_id(clean)
            return jsonify({"type": "single", "paper": paper})

        else:
            papers = fetch_by_title(query)
            return jsonify({"type": "list", "papers": papers})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    """
    Run full pipeline: prepare → summarize → (optionally) explain.
    Body: { "paper": {...}, "model": "llama-3.3-70b-versatile", "explain": true }
    """
    data    = request.get_json()
    paper   = (data or {}).get("paper")
    model   = (data or {}).get("model", "llama-3.3-70b-versatile")
    explain = (data or {}).get("explain", True)

    if not paper:
        return jsonify({"error": "paper object is required"}), 400

    try:
        # Step 1 — clean + chunk
        prepared = prepare_paper(paper)

        # Step 2 — summarize
        summary  = summarize_paper(prepared, model=model)

        # Step 3 — explain concepts (optional)
        concepts = []
        if explain:
            raw_concepts = explain_paper_concepts(prepared, summary, model=model)
            # Convert dict → list for JSON
            concepts = [{"term": t, **v} if isinstance(v, dict) else {"term": t, "explanation": v}
                        for t, v in raw_concepts.items()]

        return jsonify({
            "summary":  summary,
            "concepts": concepts,
            "meta": {
                "token_count": prepared.get("token_count", 0),
                "chunks":      len(prepared.get("chunks", [])),
                "model":       model,
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)