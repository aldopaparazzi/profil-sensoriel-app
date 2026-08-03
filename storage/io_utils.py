# storage/io_utils.py

import json

from storage.last_seen import update_last_seen
from storage.paths import paths
from utils.logger import logger


def save_raw_json(raw: dict, form_name: str, full_refresh: bool = False):
    """
    Sauvegarde les données brutes avec suivi des derniers IDs.
    """
    paths.raw_dir.mkdir(parents=True, exist_ok=True)

    submissions = raw.get("submissions", [])

    if not submissions:
        logger.warning(f"Aucune soumission pour {form_name}")
        return None

    # Lire le fichier existant
    file_path = paths.raw_dir / f"{form_name}.json"
    existing_data = {"submissions": []}

    if file_path.exists() and not full_refresh:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except (OSError, json.JSONDecodeError):
            pass

    # Récupérer les IDs existants
    existing_ids = {s.get("id") for s in existing_data.get("submissions", [])}

    # Ajouter les nouvelles soumissions (éviter les doublons)
    new_count = 0
    for sub in submissions:
        sub_id = sub.get("id")
        if sub_id and sub_id not in existing_ids:
            existing_data["submissions"].append(sub)
            new_count += 1

    # Sauvegarder
    file_path.write_text(
        json.dumps(existing_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Mettre à jour le dernier ID vu
    if submissions:
        last_sub = submissions[-1]  # Dernière soumission (la plus récente)
        last_id = last_sub.get("id")
        submitted_at = last_sub.get("submittedAt")
        if last_id:
            update_last_seen(form_name, last_id, submitted_at)

    logger.info(f"💾 {form_name} sauvegardé")
    logger.info(f"   - Nouvelles: {new_count}")
    logger.info(f"   - Total: {len(existing_data['submissions'])}")

    return file_path


def load_cached_submissions(form_name: str) -> list[dict]:
    """Charge toutes les soumissions depuis le cache."""
    file_path = paths.raw_dir / f"{form_name}.json"

    if not file_path.exists():
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("submissions", [])
    except (OSError, json.JSONDecodeError):
        return []
