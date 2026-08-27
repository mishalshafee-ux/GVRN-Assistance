import json
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path("session_state.json")


def load_state():
    if not STATE_FILE.exists():
        return {}

    with STATE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_state(state):
    with STATE_FILE.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=2)


def save_session_start(guild_id):
    state = load_state()
    state[str(guild_id)] = datetime.now(timezone.utc).isoformat()
    save_state(state)


def get_session_start(guild_id):
    state = load_state()
    started_at = state.get(str(guild_id))

    if not started_at:
        return None

    return datetime.fromisoformat(started_at)


def clear_session_start(guild_id):
    state = load_state()
    state.pop(str(guild_id), None)
    save_state(state)
