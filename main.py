# main.py
# raw → split → mapped → scores → report
# 1. Fetch Tally json
# 2. Validation
# 3. Split
# 4. Mapping
# 5. Scoring
# 6. Report
from pprint import pprint
import json

from utils.logger import log
from pipeline.validate import validate_dataset
from pipeline.split import split_dataset
from pipeline.mapping import load_reference, map_sensory_responses
from pipeline.profiling import profile_dataset
from pipeline.scoring import compute_scores

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
        "debug": config.get("debug", False),
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

    print("\n==========  DEBUG  ==============")

    # for r in clean["submissions"][0]["responses"]:
    # pprint(r)

    print("\n==========  /DEBUG  ==============")

    # =========================================================
    # 2.5 PROFILING
    # =========================================================
    #log(context, "\n2.5 🔎 Profiling")
    #
    #for form_name, clean in context["validated"].items():
    #    profile_dataset(clean, form_name)

    # =========================================================
    # 3. SPLIT
    # =========================================================
    log(context, "\n3.✂️ Split")

    for form_name, clean in context["validated"].items():
        split = split_dataset(clean)
        context["split"][form_name] = split
        # print(f"{form_name}: Éléments séparés")
    pprint(context["split"]["scolaire"][0])

    # =========================================================
    # 4. MAPPING (IMPORTANT: PAR FORM)
    # =========================================================
    log(context, "\n4.🧠 Mapping")
    for form_name, submissions in context["split"].items():
        # 3.1. Exclusion des soumissions vides
        if not submissions:
            print(f"📭 {form_name}: aucune soumission")
            continue

        print(f"📥 {form_name}: {len(submissions)} soumission(s)")
        first_submission = submissions[0]
        with open("data/reference/scolaire.json", encoding="utf-8") as f:
            reference = json.load(f)
        mapped = map_sensory_responses(first_submission["sensory_responses"], reference)

        #        pprint(mapped[:3])
        #context["mapped"][form_name] = mapped

        all_scored = []

        for form_name, submissions in context["split"].items():

            if not submissions:
                continue

            with open("data/reference/scolaire.json", encoding="utf-8") as f:
                reference = json.load(f)
                        
            mapped_submissions = []

            for submission in submissions:

                mapped_items = map_sensory_responses(
                    submission["sensory_responses"],
                    reference
                )

                mapped_submissions.append({
                    "items": mapped_items,
                    "patient": submission.get("patient", {}),
                    "respondent": submission.get("respondent", {}),
                    "metadata": submission.get("metadata", {})
                })

            for ms in mapped_submissions:
                scored = compute_scores(ms, reference)
                all_scored.append(scored)

        context["scores"] = all_scored

        print(f"{form_name}: Enrichi")


    # =========================================================
    # 5. SCORING
    # =========================================================
    log(context, "\n5.📊 Scoring")

    #context = compute_scores(context)

    #print("\nSCORES :")
    #print(context["scores"])

#    scored = compute_scores(mapped, reference)
#    scored = compute_scores(mapped_submission, reference)
#
#    # injection dans payload complet
#    final_payload = {
#        **mapped,
#        "scores": scored
#    }

    # =========================================================
    # 6. REPORT(placeholder)
    # =========================================================
    log(context, "\n6.📄 Report")

    print("\nSCORES :")
    print(context["scores"])

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
