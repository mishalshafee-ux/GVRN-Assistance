import json
import os
import secrets
from pathlib import Path

import requests
from flask import Blueprint, redirect, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


roblox_oauth = Blueprint("roblox_oauth", __name__)

DATA_DIR = Path(__file__).resolve().parent / "data"
LINKS_FILE = DATA_DIR / "roblox_links.json"

CLIENT_ID = os.getenv("ROBLOX_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("ROBLOX_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv(
    "ROBLOX_REDIRECT_URI",
    "https://gvrn.wispbyte.app/roblox/callback",
)
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
GUILD_ID = os.getenv("GUILD_ID", "")
CIVILIAN_ROLE_ID = os.getenv("CIVILIAN_ROLE_ID", "")
UNVERIFIED_ROLE_ID = os.getenv("UNVERIFIED_ROLE_ID", "")

AUTH_URL = "https://apis.roblox.com/oauth/v1/authorize"
TOKEN_URL = "https://apis.roblox.com/oauth/v1/token"
USERINFO_URL = "https://apis.roblox.com/oauth/v1/userinfo"
DISCORD_API = "https://discord.com/api/v10"

serializer = URLSafeTimedSerializer(
    SECRET_KEY,
    salt="gvrn-roblox-verification",
)


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


def page(title, message):
    return f"""
    <!doctype html>
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                background: #20242a;
                color: #f4f7fb;
                font-family: Arial, sans-serif;
                display: grid;
                place-items: center;
                min-height: 100vh;
                margin: 0;
            }}
            main {{
                max-width: 560px;
                padding: 32px;
                border: 1px solid #7EC8E3;
                border-radius: 16px;
                background: #2a3038;
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


def discord_headers():
    return {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json",
    }


def discord_url(path):
    return f"{DISCORD_API}{path}"


def update_discord_member(discord_id, roblox_name):
    if not all((
        DISCORD_TOKEN,
        GUILD_ID,
        CIVILIAN_ROLE_ID,
        UNVERIFIED_ROLE_ID,
    )):
        raise RuntimeError("Discord OAuth role settings are incomplete.")

    add_url = discord_url(
        f"/guilds/{GUILD_ID}/members/{discord_id}/roles/{CIVILIAN_ROLE_ID}"
    )
    remove_url = discord_url(
        f"/guilds/{GUILD_ID}/members/{discord_id}/roles/{UNVERIFIED_ROLE_ID}"
    )
    member_url = discord_url(
        f"/guilds/{GUILD_ID}/members/{discord_id}"
    )

    add_response = requests.put(
        add_url,
        headers=discord_headers(),
        timeout=15,
    )

    if add_response.status_code not in (200, 204):
        raise RuntimeError(
            f"Could not add Civilian role: {add_response.status_code}"
        )

    requests.delete(
        remove_url,
        headers=discord_headers(),
        timeout=15,
    )

    nickname = f"[Civilian] {roblox_name}"[:32]

    nickname_response = requests.patch(
        member_url,
        headers=discord_headers(),
        json={"nick": nickname},
        timeout=15,
    )

    nickname_changed = nickname_response.status_code in (200, 204)

    return nickname, nickname_changed


@roblox_oauth.route("/roblox/authorize")
def authorize():
    discord_id = request.args.get("discord_id", "").strip()

    if not discord_id.isdigit():
        return page("Verification error", "Invalid Discord account."), 400

    state = serializer.dumps({
        "discord_id": discord_id,
        "nonce": secrets.token_urlsafe(24),
    })

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid profile",
        "response_type": "code",
        "state": state,
    }

    query = "&".join(
        f"{key}={requests.utils.quote(str(value), safe='')}"
        for key, value in params.items()
    )

    return redirect(f"{AUTH_URL}?{query}")


@roblox_oauth.route("/roblox/callback")
def callback():
    error = request.args.get("error")

    if error:
        return page(
            "Verification cancelled",
            "Roblox authorization was cancelled.",
        )

    code = request.args.get("code")
    state = request.args.get("state")

    if not code or not state:
        return page(
            "Verification error",
            "Roblox did not return a valid authorization response.",
        ), 400

    try:
        state_data = serializer.loads(state, max_age=600)
    except (BadSignature, SignatureExpired):
        return page(
            "Verification error",
            "This verification link expired. Start again from Discord.",
        ), 400

    token_response = requests.post(
        TOKEN_URL,
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
        print(
            "Roblox token error:",
            token_response.status_code,
            token_response.text,
        )
        return page(
            "Verification error",
            "Roblox authorization could not be completed.",
        ), 502

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        return page(
            "Verification error",
            "Roblox did not return an access token.",
        ), 502

    user_response = requests.get(
        USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )

    if user_response.status_code != 200:
        print(
            "Roblox user info error:",
            user_response.status_code,
            user_response.text,
        )
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

    if not roblox_id:
        return page(
            "Verification error",
            "Roblox did not provide a user ID.",
        ), 502

    discord_id = state_data["discord_id"]

    try:
        nickname, nickname_changed = update_discord_member(
            discord_id,
            roblox_name,
        )
    except Exception as exc:
        print(f"Discord role update error: {exc}")
        return page(
            "Verification error",
            "The Roblox account was confirmed, but Discord roles "
            "could not be updated. Contact staff.",
        ), 500

    links = load_links()
    links[discord_id] = {
        "roblox_id": roblox_id,
        "roblox_name": roblox_name,
    }
    save_links(links)

    nickname_text = (
        f"Nickname changed to {nickname}."
        if nickname_changed
        else "Discord did not allow the nickname change."
    )

    return page(
        "Verification successful",
        f"Verified Roblox account: {roblox_name}. "
        f"Civilian role added. {nickname_text} "
        "You may return to Discord.",
    )
