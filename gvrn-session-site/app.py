import json
import os
import uuid
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"
LOGS_FILE = DATA_DIR / "session_logs.json"
PERSONAL_LOGS_FILE = DATA_DIR / "personal_logs.json"
TRANSCRIPTS_FILE = DATA_DIR / "ticket_transcripts.json"


def load_json(path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    DATA_DIR.mkdir(exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def ensure_admin():
    users = load_json(USERS_FILE, [])

    admin_username = os.getenv("ADMIN_USERNAME", "owners")
    admin_password = os.getenv("ADMIN_PASSWORD", "civocisthebest")

    admin = next((user for user in users if user.get("role") == "admin" and user.get("discord_user_id") == "owner-admin"), None)

    if admin:
        admin["username"] = admin_username
        admin["password_hash"] = generate_password_hash(admin_password)
    else:
        users.append({
            "id": str(uuid.uuid4()),
            "username": admin_username,
            "discord_user_id": "owner-admin",
            "password_hash": generate_password_hash(admin_password),
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    save_json(USERS_FILE, users)


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None

    users = load_json(USERS_FILE, [])
    return next((user for user in users if user["id"] == user_id), None)


def login_required(route):
    @wraps(route)
    def wrapper(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login"))
        return route(*args, **kwargs)
    return wrapper


def admin_required(route):
    @wraps(route)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or user.get("role") != "admin":
            flash("Admin access required.")
            return redirect(url_for("dashboard"))
        return route(*args, **kwargs)
    return wrapper


@app.before_request
def setup():
    ensure_admin()


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        users = load_json(USERS_FILE, [])
        user = next((u for u in users if u["username"].lower() == username.lower()), None)

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid username or password.")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    logs = load_json(LOGS_FILE, [])

    if user["role"] != "admin":
        logs = [log for log in logs if log["created_by_id"] == user["id"]]

    logs = list(reversed(logs))
    return render_template("dashboard.html", user=user, logs=logs)


@app.route("/log-session", methods=["GET", "POST"])
@login_required
def log_session():
    user = current_user()

    if request.method == "POST":
        logs = load_json(LOGS_FILE, [])

        log = {
            "id": str(uuid.uuid4()),
            "hosted_by": request.form.get("hosted_by", "").strip(),
            "duration": request.form.get("duration", "").strip(),
            "co_hosts": request.form.get("co_hosts", "").strip(),
            "notes": request.form.get("notes", "").strip(),
            "created_by_id": user["id"],
            "created_by_username": user["username"],
            "created_by_discord_user_id": user["discord_user_id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        logs.append(log)
        save_json(LOGS_FILE, logs)

        flash("Session log saved.")
        return redirect(url_for("dashboard"))

    return render_template("log_session.html", user=user)


@app.route("/admin/users", methods=["GET", "POST"])
@login_required
@admin_required
def manage_users():
    users = load_json(USERS_FILE, [])

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        discord_user_id = request.form.get("discord_user_id", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "staff")

        if not username or not discord_user_id or not password:
            flash("Username, Discord User ID, and password are required.")
            return redirect(url_for("manage_users"))

        if any(user["username"].lower() == username.lower() for user in users):
            flash("That username already exists.")
            return redirect(url_for("manage_users"))

        users.append({
            "id": str(uuid.uuid4()),
            "username": username,
            "discord_user_id": discord_user_id,
            "password_hash": generate_password_hash(password),
            "role": role,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        save_json(USERS_FILE, users)
        flash("Staff account created.")
        return redirect(url_for("manage_users"))

    return render_template("users.html", user=current_user(), users=users)

@app.route("/admin/personal-logs", methods=["GET", "POST"])
@login_required
@admin_required
def personal_logs():
    logs = load_json(PERSONAL_LOGS_FILE, [])

    if request.method == "POST":
        user = current_user()
        logs.append({
            "id": str(uuid.uuid4()),
            "title": request.form.get("title", "").strip(),
            "notes": request.form.get("notes", "").strip(),
            "created_by": user["username"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        save_json(PERSONAL_LOGS_FILE, logs)
        flash("Personal log saved.")
        return redirect(url_for("personal_logs"))

    return render_template("personal_logs.html", user=current_user(), logs=list(reversed(logs)))


@app.route("/admin/ticket-transcripts", methods=["GET", "POST"])
@login_required
@admin_required
def ticket_transcripts():
    transcripts = load_json(TRANSCRIPTS_FILE, [])

    if request.method == "POST":
        user = current_user()
        transcripts.append({
            "id": str(uuid.uuid4()),
            "ticket_name": request.form.get("ticket_name", "").strip(),
            "opened_by": request.form.get("opened_by", "").strip(),
            "closed_by": request.form.get("closed_by", "").strip(),
            "transcript": request.form.get("transcript", "").strip(),
            "saved_by": user["username"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        save_json(TRANSCRIPTS_FILE, transcripts)
        flash("Ticket transcript saved.")
        return redirect(url_for("ticket_transcripts"))

    return render_template("ticket_transcripts.html", user=current_user(), transcripts=list(reversed(transcripts)))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "3000")))
