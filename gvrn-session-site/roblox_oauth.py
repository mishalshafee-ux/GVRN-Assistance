import json
import os
import secrets
from pathlib import Path
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from flask import Blueprint, redirect, request
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired


roblox_oauth = Blueprint("roblox_oauth", __name__)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv()
print(f"Roblox OAuth client configured: {bool(os.getenv('ROBLOX_CLIENT_ID'))}")

CLIENT_ID = os.getenv("ROBLOX_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("ROBLOX_CLIENT_SECRET", "").strip()
REDIRECT_URI = os.getenv(
    "ROBLOX_REDIRECT_URI",
    "https://gvrn.wispbyte.app/roblox/callback",
)
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
GUILD_ID = os.getenv("GUILD_ID", "")
CIVILIAN_ROLE_ID = os.getenv("CIVILIAN_ROLE_ID", "")
UNVERIFIED_ROLE_ID = os.getenv("UNVERIFIED_ROLE_ID", "")

DATA_DIR = Path(__file__).resolve().parent / "data"
LINKS_FILE = DATA_DIR / "roblox_links.json"

serializer = URLSafeTimedSerializer(
    SECRET_KEY,
    salt="gvrn-roblox-oauth",
)


def page(title, message):
    return f"""
    <!doctype html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{
                background: #20242a;
                color: white;
                font-family: Arial, sans-serif;
                display: grid;
                place-items: center;
                min-height: 100vh;
            }}
            main {{
                max-width: 600px;
                padding: 32px;
                border: 1px solid #7EC8E3;
                border-radius: 16px;
                background: #2b3139;
                text-align: center;
            }}
            h1 {{ color: #7EC8E3; }}
        </style>
    </head>
    <body>
        <main>
            <h1>{title}</h1>
            <p>{message}</p>
        </main>
    </body>
    </html>
    """


def load_links():
    if not LINKS_FILE.exists():
        return {}

    try:
        return json.loads(LINKS_FILE.read_text())
    except Exception:
        return {}


def save_links(links):
    DATA_DIR.mkdir(exist_ok=True)
    LINKS_FILE.write_text(json.dumps(links, indent=2))


def discord_headers():
    return {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json",
    }


@roblox_oauth.route("/roblox/authorize")
def authorize():
    discord_id = request.args.get("discord_id", "")

    if not discord_id.isdigit():
        return page("Verification error", "Invalid Discord account."), 400

    state = serializer.dumps({
        "discord_id": discord_id,
        "nonce": secrets.token_urlsafe(24),
    })

    query = urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid profile",
        "response_type": "code",
        "state": state,
    })

    return redirect(
        f"https://apis.roblox.com/oauth/v1/authorize?{query}"
    )


@roblox_oauth.route("/roblox/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if not code or not state:
        return page(
            "Verification error",
            "Roblox authorization was incomplete.",
        ), 400

    try:
        state_data = serializer.loads(state, max_age=600)
    except (BadSignature, SignatureExpired):
        return page(
            "Verification error",
            "This verification link expired. Start again from Discord.",
        ), 400

    token_response = requests.post(
        "https://apis.roblox.com/oauth/v1/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )

    if token_response.status_code != 200:
        print("Roblox token error:", token_response.text)
        return page(
            "Verification error",
            "Roblox authorization failed.",
        ), 502

    access_token = token_response.json().get("access_token")

    user_response = requests.get(
        "https://apis.roblox.com/oauth/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )

    if user_response.status_code != 200:
        print("Roblox user error:", user_response.text)
        return page(
            "Verification error",
            "Roblox account information could not be read.",
        ), 502

    user_data = user_response.json()
    roblox_id = str(user_data.get("sub", ""))
    roblox_name = (
        user_data.get("preferred_username")
        or user_data.get("name")
        or "Roblox User"
    )
    discord_id = state_data["discord_id"]

    if not roblox_id:
        return page(
            "Verification error",
            "Roblox did not return a user ID.",
        ), 502

    role_url = (
        f"https://discord.com/api/v10/guilds/{GUILD_ID}"
        f"/members/{discord_id}/roles/{CIVILIAN_ROLE_ID}"
    )

    role_response = requests.put(
        role_url,
        headers=discord_headers(),
        timeout=15,
    )

    if role_response.status_code not in (200, 204):
        print("Discord role error:", role_response.text)
        return page(
            "Verification error",
            "The Civilian role could not be added.",
        ), 500

    remove_url = (
        f"https://discord.com/api/v10/guilds/{GUILD_ID}"
        f"/members/{discord_id}/roles/{UNVERIFIED_ROLE_ID}"
    )

    requests.delete(
        remove_url,
        headers=discord_headers(),
        timeout=15,
    )

    member_url = (
        f"https://discord.com/api/v10/guilds/{GUILD_ID}"
        f"/members/{discord_id}"
    )

    requests.patch(
        member_url,
        headers=discord_headers(),
        json={"nick": f"[Civilian] {roblox_name}"[:32]},
        timeout=15,
    )

    links = load_links()
    links[discord_id] = {
        "roblox_id": roblox_id,
        "roblox_name": roblox_name,
    }
    save_links(links)

    return page(
        "Verification successful",
        f"Verified as {roblox_name}. The Civilian role was added.",
    )
