# main.py
# raw → split → mapped → scores → report
# 1. Fetch Tally json
# 2. Validation
# 3. Split
# 4. Mapping
# 5. Scoring
# 6. Report
from pprint import pprint

from utils.logger import log
from pipeline.validate import validate_dataset
from pipeline.split import split_dataset
from pipeline.mapping import load_reference, map_questions, map_sensory_responses
from ingestion.fetch_tally import fetch_tally, TallyAPIError
from storage.io_utils import save_raw_json

from config.settings import load_config, replace_tally_token


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

    token = config["tally_token"]

    log(context, "1.📥 Fetch Tally")

    # =========================================================
    # 1. INGESTION + RAW
    # =========================================================
    for form_name, form_id in config["forms"].items():

        try:
            raw = fetch_tally(form_id, token)

        except TallyAPIError as e:

            if e.status_code == 401:
                print("\n⚠️ Token Tally invalide")
                token = replace_tally_token()

                raw = fetch_tally(form_id, token)

            else:
                error_msg = f"[{form_name}] {str(e)}"
                context["errors"].append(error_msg)
                continue

        save_raw_json(raw, form_name)
        context["raw"][form_name] = raw

        print(f"{form_name}: À jour")


    if not context["raw"]:
        print("\n⛔ Aucun formulaire récupéré. Arrêt pipeline.")
        return

    # =========================================================
    # 2. VALIDATION
    # =========================================================
    log(context, "\n2.🧹 Validation")

    for form_name, raw in context["raw"].items():
        clean = validate_dataset(raw, context)
        context["validated"][form_name] = clean
        print(f"{form_name}: Données validé")
        

    # =========================================================
    # 3. SPLIT
    # =========================================================
    log(context, "\n3.✂️ Split")

    for form_name, clean in context["validated"].items():
        split = split_dataset(clean)
        context["split"][form_name] = split
        print(f"{form_name}: Éléments séparés")


    # =========================================================
    # 4. MAPPING (IMPORTANT: PAR FORM)
    # =========================================================
    log(context, "\n4.🧠 Mapping")
    for form_name, submissions in context["split"].items():

    # 3.1. Exclusion des soumissions vides
        if not submissions:
            print(f"📭 {form_name}: aucune soumission")
            continue

        print(
            f"📥 {form_name}: "
            f"{len(submissions)} soumission(s)"
        )
        first_submission = submissions[0]
        reference = load_reference(f"data/reference/{form_name}.csv")

        mapped = map_sensory_responses(
            first_submission["sensory_responses"],
            reference
        )

#        pprint(mapped[:3])
        context["mapped"][form_name] = mapped
        print(f"{form_name}: Enrichi")

    # =========================================================
    # 5. SCORING (placeholder)
    # =========================================================
    log(context, "\n5.📊 Scoring")

    context["scores"] = {
        "RE": 0,
        "EV": 0,
        "SE": 0,
        "EN": 0
    }

    # =========================================================
    # 6. REPORT
    # =========================================================
    log(context, "\n6.📄 Report")

    print("\nSCORES :")
    print(context["scores"])

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()