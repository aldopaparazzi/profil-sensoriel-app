import json
from pathlib import Path

STATE_PATH = Path("data/raw/.state.json")


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {}


def save_state(state):
    STATE_PATH.write_text(
        json.dumps(state, indent=2),
        encoding="utf-8"
    )