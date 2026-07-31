import json

from storage.paths import paths


def load_state():
    if paths.state_file.exists():
        return json.loads(paths.state_file.read_text(encoding="utf-8"))
    return {}


def save_state(state):
    paths.state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
