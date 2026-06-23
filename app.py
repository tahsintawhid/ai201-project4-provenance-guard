from flask import Flask, request, jsonify
from dotenv import load_dotenv
from db import init_db
from pipeline import analyze
from audit import write_log_entry, get_log
import uuid

load_dotenv()

app = Flask(__name__)
init_db()


@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()

    if not data or "text" not in data or "creator_id" not in data:
        return jsonify({"error": "Request must include 'text' and 'creator_id' fields."}), 400

    text = data["text"]
    creator_id = data["creator_id"]
    content_id = str(uuid.uuid4())

    result = analyze(text)

    write_log_entry(
        content_id=content_id,
        creator_id=creator_id,
        content_preview=text[:120],
        llm_score=result["llm_score"],
        stylometric_score=result["stylometric_score"],
        combined_score=result["combined_score"],
        attribution_result=result["attribution_result"],
        confidence_label=result["confidence_label"],
        transparency_label=result["transparency_label"],
        status="reviewed"
    )

    return jsonify({
        "content_id": content_id,
        "attribution": result["attribution_result"],
        "confidence": result["combined_score"],
        "confidence_label": result["confidence_label"],
        "label": result["transparency_label"],
        "llm_score": result["llm_score"],
        "llm_reasoning": result["llm_reasoning"],
        "stylometric_score": result["stylometric_score"],
        "stylometric_metrics": result["stylometric_metrics"]
    }), 200


@app.route("/log", methods=["GET"])
def log():
    entries = get_log()
    return jsonify({"entries": entries}), 200


if __name__ == "__main__":
    app.run(debug=True)
