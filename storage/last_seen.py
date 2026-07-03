import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

LAST_SEEN_FILE = Path("data/raw/.last_seen.json")

def load_last_seen() -> Dict[str, dict]:
    """Charge les derniers IDs et dates pour chaque formulaire."""
    if LAST_SEEN_FILE.exists():
        with open(LAST_SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_last_seen(data: dict):
    """Sauvegarde les derniers IDs et dates."""
    LAST_SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LAST_SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_last_seen(form_name: str) -> Optional[dict]:
    """Récupère les infos du dernier ID vu pour un formulaire."""
    data = load_last_seen()
    return data.get(form_name)

def update_last_seen(form_name: str, submission_id: str, submitted_at: str):
    """Met à jour le dernier ID vu pour un formulaire."""
    data = load_last_seen()
    data[form_name] = {
        "last_id": submission_id,
        "last_date": submitted_at,
        "updated_at": datetime.now().isoformat()
    }
    save_last_seen(data)