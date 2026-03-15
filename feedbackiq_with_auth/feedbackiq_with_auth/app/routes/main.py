"""
app/routes/main.py
Main web page routes — all protected by login_required
"""

from flask import Blueprint, render_template, session
from app.auth import login_required
from app.database import AnalysisRepository
from flask import current_app

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index():
    return render_template("index.html")


@main_bp.route("/upload")
@login_required
def upload():
    return render_template("upload.html")


@main_bp.route("/results")
@login_required
def results():
    return render_template("results.html")


@main_bp.route("/history")
@login_required
def history():
    repo = AnalysisRepository(db_path=current_app.config.get("DB_PATH"))
    uid  = None if session.get("role") == "admin" else session.get("user_id")
    analyses = repo.get_all(user_id=uid, limit=200)
    return render_template("history.html", analyses=analyses)


@main_bp.route("/audit-log")
@login_required
def audit_log():
    return render_template("audit_log.html")


@main_bp.route("/about")
@login_required
def about():
    return render_template("about.html")
