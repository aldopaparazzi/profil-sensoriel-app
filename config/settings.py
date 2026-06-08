# config/settings.py
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "runtime.json"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)