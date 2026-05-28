from pathlib import Path
from datetime import datetime
from storage.data_fingerprint import dataframe_hash
from storage.state import load_state, save_state

RAW_DIR = Path("data/raw")


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