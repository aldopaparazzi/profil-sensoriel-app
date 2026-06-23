import json
from pathlib import Path
from datetime import datetime
from storage.data_fingerprint import dataframe_hash, json_hash
from storage.state import load_state, save_state

RAW_DIR = Path("data/raw")
MAPPED_DIR = Path("data/mapped")
SCORED_DIR = Path("data/scored")


def save_scored_json(data: dict, form_name: str):
    """
    Sauvegarde les données scoré dans data/mapped/.

    Args:
        data: dict (scored output du pipeline)
        form_name: str (nom du formulaire)
    """

    # =========================================================
    # 1. création dossier si besoin
    # =========================================================
    SCORED_DIR.mkdir(parents=True, exist_ok=True)

    # =========================================================
    # 2. timestamp
    # =========================================================
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # =========================================================
    # 3. nom de fichier
    # =========================================================
    filename = f"{form_name}.json" #_{timestamp}.json"
    path = SCORED_DIR / filename

    # =========================================================
    # 4. sauvegarde JSON
    # =========================================================
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"💾 SCORED JSON sauvegardé : {path}")

    return path

def save_mapped_json(data: dict, form_name: str):
    """
    Sauvegarde les données mappées dans data/mapped/.

    Args:
        data: dict (mapped output du pipeline)
        form_name: str (nom du formulaire)
    """

    # =========================================================
    # 1. création dossier si besoin
    # =========================================================
    MAPPED_DIR.mkdir(parents=True, exist_ok=True)

    # =========================================================
    # 2. timestamp
    # =========================================================
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # =========================================================
    # 3. nom de fichier
    # =========================================================
    filename = f"{form_name}.json" #_{timestamp}.json"
    path = MAPPED_DIR / filename

    # =========================================================
    # 4. sauvegarde JSON
    # =========================================================
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"💾 MAPPED JSON sauvegardé : {path}")

    return path

def normalize_raw(raw: dict) -> dict:

    normalized = {
        "submissions": []
    }

    for sub in raw.get("submissions", []):

        cleaned_sub = {
            "id": sub.get("id"),
            "formId": sub.get("formId"),
            "submittedAt": sub.get("submittedAt"),
            "responses": []
        }

        for r in sub.get("responses", []):

            cleaned_sub["responses"].append({
                "questionId": r.get("questionId"),
                "answer": r.get("answer")
            })

        # IMPORTANT: tri stable des responses
        cleaned_sub["responses"] = sorted(
            cleaned_sub["responses"],
            key=lambda x: x["questionId"]
        )

        normalized["submissions"].append(cleaned_sub)

    # IMPORTANT: tri stable des submissions aussi
    normalized["submissions"] = sorted(
        normalized["submissions"],
        key=lambda x: x["id"]
    )

    return normalized

def save_raw_json(raw, form_name: str, full_refresh: bool = False):
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    current_hash = json_hash(normalize_raw(raw))

    state = load_state()
    last_hash = state.get(form_name)

    # =========================================================
    # FULL REFRESH → ignore hash
    # =========================================================
    if not full_refresh and last_hash == current_hash:
        print(f"\n⏭️  {form_name} inchangé → skip RAW")
        return None

    # =========================================================
    #  NOMS DE FICHIERS
    # =========================================================
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    file_last = RAW_DIR / f"{form_name}.json"
    file_archived = RAW_DIR / f"{form_name}_{timestamp}.json"

    # =========================================================
    # 1. ARCHIVE (timestamp)
    # =========================================================
    file_archived.write_text(
        json.dumps(raw, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # =========================================================
    # 2. LAST (overwrite)
    # =========================================================
    file_last.write_text(
        json.dumps(raw, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    # =========================================================
    # UPDATE STATE
    # =========================================================
    state[form_name] = current_hash
    save_state(state)

    print(f"💾 RAW JSON sauvegardé : {file_last}")
    print(f"   - archive : {file_archived}")
    print(f"   - last    : {file_last}")
    
    print("\n=== HASH DEBUG ===")
    print("FORM:", form_name)
    print("CURRENT:", current_hash)
    print("LAST:", last_hash)
    print("==================\n")
    return file_last
