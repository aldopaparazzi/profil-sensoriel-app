# main.py
# raw → split → mapped → scores → report
# 1. Fetch Tally json
# 2. Validation
# 3. Split
# 4. Mapping
# 5. Scoring
# 6. Report

from config.settings import load_config
from utils.logger import log
from ingestion.fetch_tally import fetch_tally, TallyAPIError
from pipeline.validate import validate_dataset

def main():

    print("\n=== PROFIL SENSORIEL V1 ===\n")

    config = load_config()

    context = {
        "raw": {},
        "validated": {},
        "split": {},
        "mapped": {},
        "scores": {},
        "errors": [],
        "debug": config.get("debug", False)
    }

    log(context, "1.📥 Fetch Tally") 
    token = config["tally_token"]

    for form_name, form_id in config["forms"].items():

        try:
            df = fetch_tally(form_id, token)
            context["raw"][form_name] = df
            log(context, df)

        except TallyAPIError as e:
            error_msg = f"[{form_name}] {str(e)}"
            print("❌", error_msg)

            context["errors"].append(error_msg)

    # =========================================================
    # STOP LOGIQUE SI ERREUR CRITIQUE
    # =========================================================
    if not context["raw"]:
        print("\n⛔ Aucun formulaire récupéré. Arrêt pipeline.")
        return

    # =========================================================
    # 2. VALIDATION
    # =========================================================
    for form_name, df in context["raw"].items():
        log(context, f"2.🧹 Validation {form_name} ({len(df)} lignes)")
        context["validated"][form_name] = validate_dataset(df, context)

    for k, df in context["validated"].items():
        print(f"{k}: {len(df)} lignes validées")

    # =========================================================
    # NEXT STEPS (placeholders)
    # =========================================================
    log(context, "3.✂️ Split")
    log(context, "4.🧠 Mapping")
    log(context, "5.📊 Scoring")
    log(context, "6.📄 Report")

    context["scores"] = {
        "RE": 0,
        "EV": 0,
        "SE": 0,
        "EN": 0
    }

    print("\nSCORES :")
    print(context["scores"])

    print("\n=== DONE ===")

if __name__ == "__main__":
    main()
