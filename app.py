from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from db import init_db
from pipeline import analyze
from audit import write_log_entry, get_log, update_status, write_appeal
import uuid

load_dotenv()

app = Flask(__name__)
init_db()

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)


@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
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


@app.route("/appeal", methods=["POST"])
def appeal():
    data = request.get_json()

    if not data or "content_id" not in data or "creator_reasoning" not in data:
        return jsonify({"error": "Request must include 'content_id' and 'creator_reasoning' fields."}), 400

    content_id = data["content_id"]
    creator_reasoning = data["creator_reasoning"]

    found = update_status(content_id, "under_review")
    if not found:
        return jsonify({"error": f"No submission found with content_id '{content_id}'."}), 404

    accepted = write_appeal(content_id, creator_reasoning)
    if not accepted:
        return jsonify({
            "message": "An open appeal already exists for this content.",
            "content_id": content_id,
            "status": "under_review"
        }), 200

    return jsonify({
        "message": "Appeal received. Your submission has been marked as under review.",
        "content_id": content_id,
        "status": "under_review"
    }), 200


@app.route("/log", methods=["GET"])
def log():
    entries = get_log()
    return jsonify({"entries": entries}), 200


if __name__ == "__main__":
    app.run(debug=True)
