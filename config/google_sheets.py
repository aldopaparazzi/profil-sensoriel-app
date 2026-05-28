# config/__init__.py
from pathlib import Path
import json

CONFIG_DIR = Path(__file__).resolve().parent

def load_sources():
    path = CONFIG_DIR / "source.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

GOOGLE_SHEETS = load_sources()