"""
app/routes/api.py
REST API endpoints — analysis + audit log
"""

import os, json, traceback
from flask import Blueprint, request, jsonify, current_app, session
from werkzeug.utils import secure_filename

from app.auth import login_required
from app.modules.preprocessor  import TextPreprocessor
from app.modules.sentiment      import SentimentAnalyzer
from app.modules.theme_extractor import ThemeExtractor
from app.modules.insight_generator import InsightGenerator
from app.modules.visualizer     import Visualizer
from app.database import AnalysisRepository

api_bp = Blueprint("api", __name__)


def allowed_file(filename):
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"csv", "txt", "json"})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def _run_pipeline(feedback_list):
    preprocessor  = TextPreprocessor()
    sentiment_analyzer = SentimentAnalyzer()
    theme_extractor    = ThemeExtractor()
    insight_generator  = InsightGenerator()
    visualizer         = Visualizer()

    cleaned    = preprocessor.process_batch(feedback_list)
    sentiments = sentiment_analyzer.analyze_batch(feedback_list)
    themes     = theme_extractor.extract(cleaned)
    insights   = insight_generator.generate(sentiments, themes, feedback_list)
    charts     = visualizer.generate_all(sentiments, themes)

    return {
        "total_feedback": len(feedback_list),
        "sentiments": sentiments,
        "themes":     themes,
        "insights":   insights,
        "charts":     charts,
    }


def _save_to_db(result, source="text", filename=None):
    """Persist result; silently skip if no DB_PATH configured."""
    try:
        repo = AnalysisRepository(db_path=current_app.config.get("DB_PATH"))
        result["source"]   = source
        result["filename"] = filename
        analysis_id = repo.save(result, user_id=session.get("user_id"))
        return analysis_id
    except Exception:
        traceback.print_exc()
        return None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@api_bp.route("/analyze/text", methods=["POST"])
@login_required
def analyze_text():
    data = request.get_json(silent=True)
    if not data or "feedback" not in data:
        return jsonify({"error": "Provide a JSON body with a 'feedback' list."}), 400
    feedback_list = data["feedback"]
    if not isinstance(feedback_list, list) or len(feedback_list) == 0:
        return jsonify({"error": "'feedback' must be a non-empty list of strings."}), 400
    try:
        result = _run_pipeline(feedback_list)
        analysis_id = _save_to_db(result, source="text")
        result["analysis_id"] = analysis_id
        return jsonify(result), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


@api_bp.route("/analyze/file", methods=["POST"])
@login_required
def analyze_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request."}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Use CSV, TXT, or JSON."}), 400

    filename    = secure_filename(file.filename)
    upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(upload_path)

    try:
        ext           = filename.rsplit(".", 1)[1].lower()
        feedback_list = _parse_file(upload_path, ext)
        if not feedback_list:
            return jsonify({"error": "No feedback found in the uploaded file."}), 400
        result = _run_pipeline(feedback_list)
        analysis_id = _save_to_db(result, source="file", filename=filename)
        result["analysis_id"] = analysis_id
        return jsonify(result), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


def _parse_file(path, ext):
    if ext == "txt":
        with open(path, "r", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]
    if ext == "json":
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, list):
            return [item if isinstance(item, str) else item.get("text","") for item in raw if item]
        raise ValueError("JSON file must contain a list.")
    if ext == "csv":
        import csv
        items = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row: items.append(row[0].strip())
        return items
    raise ValueError(f"Unsupported extension: {ext}")


@api_bp.route("/analyses", methods=["GET"])
@login_required
def list_analyses():
    repo = AnalysisRepository(db_path=current_app.config.get("DB_PATH"))
    uid  = None if session.get("role") == "admin" else session.get("user_id")
    rows = repo.get_all(user_id=uid)
    return jsonify({"total": len(rows), "analyses": rows}), 200


@api_bp.route("/analyses/<int:analysis_id>", methods=["GET"])
@login_required
def get_analysis(analysis_id):
    repo = AnalysisRepository(db_path=current_app.config.get("DB_PATH"))
    row  = repo.get_by_id(analysis_id)
    if not row:
        return jsonify({"error": "Analysis not found."}), 404
    if session.get("role") != "admin" and row.get("created_by") != session.get("user_id"):
        return jsonify({"error": "Access denied."}), 403
    return jsonify(row), 200


@api_bp.route("/analyses/<int:analysis_id>", methods=["DELETE"])
@login_required
def delete_analysis(analysis_id):
    repo = AnalysisRepository(db_path=current_app.config.get("DB_PATH"))
    row  = repo.get_by_id(analysis_id)
    if not row:
        return jsonify({"error": "Not found."}), 404
    if session.get("role") != "admin" and row.get("created_by") != session.get("user_id"):
        return jsonify({"error": "Access denied."}), 403
    repo.delete(analysis_id, user_id=session.get("user_id"))
    return jsonify({"deleted": True}), 200


@api_bp.route("/stats", methods=["GET"])
@login_required
def stats():
    repo = AnalysisRepository(db_path=current_app.config.get("DB_PATH"))
    uid  = None if session.get("role") == "admin" else session.get("user_id")
    return jsonify(repo.get_stats(user_id=uid)), 200


@api_bp.route("/audit-log", methods=["GET"])
@login_required
def audit_log():
    repo = AnalysisRepository(db_path=current_app.config.get("DB_PATH"))
    uid  = None if session.get("role") == "admin" else session.get("user_id")
    rows = repo.get_audit_log(limit=100, user_id=uid)
    return jsonify({"total": len(rows), "log": rows}), 200


@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "FeedbackIQ API is running."}), 200
