import json
from pathlib import Path
from datetime import datetime
from storage.data_fingerprint import dataframe_hash, json_hash
from storage.state import load_state, save_state

RAW_DIR = Path("data/raw")

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
        print(f"⏭️  {form_name} inchangé → skip RAW")
        return None

    # =========================================================
    # SAVE RAW
    # =========================================================
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{form_name}_{timestamp}.json"
    path = RAW_DIR / filename

    path.write_text(
        json.dumps(raw, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # =========================================================
    # UPDATE STATE
    # =========================================================
    state[form_name] = current_hash
    save_state(state)

    print(f"💾 RAW JSON sauvegardé : {path}")

    print("\n=== HASH DEBUG ===")
    print("FORM:", form_name)
    print("CURRENT:", current_hash)
    print("LAST:", last_hash)
    print("==================\n")
    return path

def save_raw_csv(df, form_name):
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    current_hash = dataframe_hash(df)

    state = load_state()
    last_hash = state.get(form_name)

    # 🔥 CAS 1 : pas de changement
    if last_hash == current_hash:
        print(f"⏭️ {form_name} inchangé → skip RAW")
        return None

    # 🔥 CAS 2 : changement détecté → save
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{form_name}_{timestamp}.csv"

    path = RAW_DIR / filename
    df.to_csv(path, index=False)

    # update state
    state[form_name] = current_hash
    save_state(state)

    print(f"💾 RAW sauvegardé : {path}")

    return path