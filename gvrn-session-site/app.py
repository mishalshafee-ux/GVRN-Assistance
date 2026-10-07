import json
import os
import uuid
import requests
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"
LOGS_FILE = DATA_DIR / "session_logs.json"
LICENSE_QUIZ_FILE = DATA_DIR / "license_quiz_applications.json"
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

    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "civocisthebest")

    admin = next((user for user in users if user.get("role") == "admin"), None)

    if admin:
        admin["username"] = admin_username
        admin["discord_user_id"] = "owner-admin"
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

@app.route("/api/ticket-transcripts", methods=["POST"])
def api_ticket_transcripts():
    api_key = os.getenv("TICKET_TRANSCRIPT_API_KEY", "")
    sent_key = request.headers.get("X-API-Key", "")

    if api_key and sent_key != api_key:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    transcripts = load_json(TRANSCRIPTS_FILE, [])

    transcripts.append({
        "id": str(uuid.uuid4()),
        "ticket_name": data.get("ticket_name", ""),
        "opened_by": data.get("opened_by", ""),
        "closed_by": data.get("closed_by", ""),
        "claimed_by": data.get("claimed_by", ""),
        "transcript": data.get("transcript", ""),
        "saved_by": "Discord Bot",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    save_json(TRANSCRIPTS_FILE, transcripts)
    return jsonify({"saved": True})

LICENSE_QUIZ_QUESTIONS = [
    "What is your Roblox username?",
    "What is your Discord User ID?",
    "Are you 13 years old or older?",
    "What does a red traffic light mean?",
    "What does a yellow traffic light mean?",
    "What should you do when approaching a stop sign?",
    "What is the purpose of a speed limit?",
    "When should you use your turn signal?",
    "What should you do when an emergency vehicle approaches with lights and sirens?",
    "What does reckless driving mean?",
    "What should you do before changing lanes?",
    "What is tailgating?",
    "When is it appropriate to use your vehicle's horn?",
    "What should you do if you are involved in a traffic accident?",
    "Why is following traffic laws important during roleplay?",
]

def send_license_result_webhook(application, decision, reason, reviewer):
    webhook_url = os.getenv("LICENSE_RESULT_WEBHOOK_URL", "")
    if not webhook_url:
        return

    answers = application.get("answers", {})
    roblox = answers.get("What is your Roblox username?", "Unknown")
    discord_id = answers.get("What is your Discord User ID?", "Unknown")

    content = (
        f"**License Quiz {decision}**\n"
        f"**Roblox Username:** {roblox}\n"
        f"**Discord User ID:** {discord_id}\n"
        f"**Reviewed By:** {reviewer}\n"
        f"**Reason:** {reason}"
    )

    try:
        requests.post(webhook_url, json={"content": content}, timeout=10)
    except Exception as error:
        print(f"Failed to send license result webhook: {error}")


@app.route("/license-quiz", methods=["GET", "POST"])
def license_quiz():
    if request.method == "POST":
        applications = load_json(LICENSE_QUIZ_FILE, [])

        answers = {}
        for index, question in enumerate(LICENSE_QUIZ_QUESTIONS):
            answers[question] = request.form.get(f"question_{index}", "").strip()

        applications.append({
            "id": str(uuid.uuid4()),
            "answers": answers,
            "status": "Pending",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        })

        save_json(LICENSE_QUIZ_FILE, applications)
        return render_template("license_quiz_submitted.html")

    return render_template("license_quiz.html", questions=LICENSE_QUIZ_QUESTIONS)


@app.route("/admin/license-quiz")
@login_required
@admin_required
def admin_license_quiz():
    applications = load_json(LICENSE_QUIZ_FILE, [])
    return render_template("admin_license_quiz.html", user=current_user(), applications=list(reversed(applications)))

@app.route("/apply")
def apply_dashboard():
    return render_template("apply_dashboard.html")

@app.route("/admin/license-quiz/<application_id>/review", methods=["POST"])
@login_required
@admin_required
def review_license_quiz(application_id):
    applications = load_json(LICENSE_QUIZ_FILE, [])
    decision = request.form.get("decision", "").strip()
    reason = request.form.get("reason", "").strip()

    application = next((item for item in applications if item.get("id") == application_id), None)

    if not application:
        flash("Application not found.")
        return redirect(url_for("admin_license_quiz"))

    if decision not in ["Accepted", "Denied"]:
        flash("Invalid decision.")
        return redirect(url_for("admin_license_quiz"))

    application["status"] = decision
    application["review_reason"] = reason
    application["reviewed_by"] = current_user()["username"]
    application["reviewed_at"] = datetime.now(timezone.utc).isoformat()

    save_json(LICENSE_QUIZ_FILE, applications)
    send_license_result_webhook(application, decision, reason, current_user()["username"])

    flash(f"Application {decision.lower()}.")
    return redirect(url_for("admin_license_quiz"))


if __name__ == "__main__":
    print("STAFF PORTAL ROUTES:", sorted(str(rule) for rule in app.url_map.iter_rules()))
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "3000")))
