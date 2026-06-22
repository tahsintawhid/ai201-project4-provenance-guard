from flask import Flask, request, jsonify
from dotenv import load_dotenv
from db import init_db
from detection.llm_signal import get_llm_score
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

    llm_result = get_llm_score(text)
    llm_score = llm_result["score"]

    # Milestone 3: placeholders until pipeline is wired in M4
    combined_score = llm_score
    attribution_result = "likely_ai" if llm_score >= 0.65 else ("uncertain" if llm_score >= 0.36 else "likely_human")
    confidence_label = "placeholder"
    transparency_label = "Full label coming in Milestone 4."

    write_log_entry(
        content_id=content_id,
        creator_id=creator_id,
        content_preview=text[:120],
        llm_score=llm_score,
        stylometric_score=None,
        combined_score=combined_score,
        attribution_result=attribution_result,
        confidence_label=confidence_label,
        transparency_label=transparency_label,
        status="reviewed"
    )

    return jsonify({
        "content_id": content_id,
        "attribution": attribution_result,
        "confidence": round(combined_score, 4),
        "label": transparency_label,
        "llm_score": round(llm_score, 4),
        "llm_reasoning": llm_result["reasoning"]
    }), 200


@app.route("/log", methods=["GET"])
def log():
    entries = get_log()
    return jsonify({"entries": entries}), 200


if __name__ == "__main__":
    app.run(debug=True)
