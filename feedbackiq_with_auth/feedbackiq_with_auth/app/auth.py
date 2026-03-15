"""
app/auth.py
Authentication Blueprint
-------------------------
Handles login, logout, registration, profile, password change,
and admin user management — modelled exactly after EmailIQ.
"""

from functools import wraps
from flask import (Blueprint, current_app, render_template,
                   request, redirect, url_for, session, flash, jsonify)
from app.database import UserRepository

auth_bp = Blueprint("auth", __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _repo() -> UserRepository:
    return UserRepository(db_path=current_app.config["DB_PATH"])


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return decorated


def current_user():
    uid = session.get("user_id")
    return _repo().get_by_id(uid) if uid else None


# ── Login ─────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("main.index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = _repo().verify_password(username, password)
        if user:
            session.permanent = True
            session["user_id"]   = user["id"]
            session["username"]  = user["username"]
            session["role"]      = user["role"]
            session["full_name"] = user["full_name"]
            _repo().update_last_login(user["id"])
            flash(f"Welcome back, {user['full_name'] or user['username']}! 👋", "success")
            next_page = request.args.get("next") or url_for("main.index")
            return redirect(next_page)
        else:
            error = "Invalid username or password. Please try again."

    return render_template("auth/login.html", error=error)


# ── Register ──────────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("main.index"))

    errors = {}
    form   = {}

    if request.method == "POST":
        form = {
            "username":  request.form.get("username",  "").strip(),
            "full_name": request.form.get("full_name", "").strip(),
            "password":  request.form.get("password",  ""),
            "confirm":   request.form.get("confirm",   ""),
        }

        if not form["username"]:
            errors["username"] = "Username is required."
        elif len(form["username"]) < 3:
            errors["username"] = "Username must be at least 3 characters."
        elif not form["username"].isalnum():
            errors["username"] = "Username can only contain letters and numbers."
        elif _repo().get_by_username(form["username"]):
            errors["username"] = "That username is already taken."

        if not form["full_name"]:
            errors["full_name"] = "Full name is required."

        if not form["password"]:
            errors["password"] = "Password is required."
        elif len(form["password"]) < 6:
            errors["password"] = "Password must be at least 6 characters."

        if form["password"] and form["password"] != form["confirm"]:
            errors["confirm"] = "Passwords do not match."

        if not errors:
            _repo().create(
                username  = form["username"],
                password  = form["password"],
                role      = "analyst",          # self-registered → analyst
                full_name = form["full_name"],
            )
            flash("Account created successfully! Please sign in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html", errors=errors, form=form)


# ── Logout ────────────────────────────────────────────────────────────────────

@auth_bp.route("/logout")
def logout():
    name = session.get("full_name") or session.get("username", "")
    session.clear()
    flash(f"You've been signed out{', ' + name if name else ''}. See you soon!", "info")
    return redirect(url_for("auth.login"))


# ── Profile ───────────────────────────────────────────────────────────────────

@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    repo    = _repo()
    error   = None
    success = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "change_password":
            current_pw = request.form.get("current_password", "")
            new_pw     = request.form.get("new_password", "")
            confirm_pw = request.form.get("confirm_password", "")
            if not repo.verify_password(session["username"], current_pw):
                error = "Current password is incorrect."
            elif len(new_pw) < 6:
                error = "New password must be at least 6 characters."
            elif new_pw != confirm_pw:
                error = "New passwords do not match."
            else:
                repo.change_password(session["user_id"], new_pw)
                success = "Password changed successfully."

        elif action == "update_name":
            full_name = request.form.get("full_name", "").strip()
            if not full_name:
                error = "Full name cannot be empty."
            else:
                repo.update_full_name(session["user_id"], full_name)
                session["full_name"] = full_name
                success = "Display name updated."

    user = repo.get_by_id(session["user_id"])
    return render_template("auth/profile.html", user=user, error=error, success=success)


# ── Admin — User Management ───────────────────────────────────────────────────

@auth_bp.route("/admin/users")
@admin_required
def admin_users():
    users = _repo().get_all()
    return render_template("auth/admin_users.html", users=users)


@auth_bp.route("/admin/users/create", methods=["POST"])
@admin_required
def admin_create_user():
    username  = request.form.get("username",  "").strip()
    password  = request.form.get("password",  "")
    role      = request.form.get("role",      "analyst")
    full_name = request.form.get("full_name", "").strip()
    if not username or not password:
        flash("Username and password are required.", "error")
    elif len(password) < 6:
        flash("Password must be at least 6 characters.", "error")
    else:
        try:
            _repo().create(username, password, role, full_name)
            flash(f"User '{username}' created successfully.", "success")
        except Exception as e:
            flash(f"Username already exists or error: {e}", "error")
    return redirect(url_for("auth.admin_users"))


@auth_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    if user_id == session["user_id"]:
        flash("You cannot delete your own account.", "error")
    else:
        _repo().delete(user_id)
        flash("User deleted.", "success")
    return redirect(url_for("auth.admin_users"))


@auth_bp.route("/admin/users/<int:user_id>/reset-password", methods=["POST"])
@admin_required
def admin_reset_password(user_id):
    new_pw = request.form.get("new_password", "")
    if len(new_pw) < 6:
        flash("Password must be at least 6 characters.", "error")
    else:
        _repo().change_password(user_id, new_pw)
        flash("Password reset successfully.", "success")
    return redirect(url_for("auth.admin_users"))


# ── User JSON API ─────────────────────────────────────────────────────────────

@auth_bp.route("/api/users")
@login_required
def api_users():
    repo  = _repo()
    users = repo.get_all() if session.get("role") == "admin" else \
            ([repo.get_by_id(session["user_id"])] if repo.get_by_id(session["user_id"]) else [])
    safe  = [{k: v for k, v in u.items() if k != "password_hash"} for u in users]
    return jsonify({"total": len(safe), "users": safe}), 200


@auth_bp.route("/api/users/<int:user_id>")
@login_required
def api_user_detail(user_id):
    if session.get("role") != "admin" and session["user_id"] != user_id:
        return jsonify({"error": "Access denied"}), 403
    u = _repo().get_by_id(user_id)
    if not u:
        return jsonify({"error": "User not found"}), 404
    u.pop("password_hash", None)
    return jsonify(u), 200
