# main.py

# raw → split → mapped → scores → report
# 1. Fetch Tally json
# 2. Validation
# 3. Split
# 4. Mapping
# 5. Scoring
# 6. Report

import json
from pprint import pprint
from config.settings import load_config, replace_tally_token
from ingestion.fetch_tally import fetch_tally, TallyAPIError
from storage.io_utils import save_raw_json
from pipeline.validate import filter_empty_submissions
from pipeline.split import split_dataset
from pipeline.mapping import map_submission, enrich_patient
from pipeline.scoring import compute_all_scores # compute_domain_scores
from reporting.report import build_final_report, export_report
from core.age import load_age_bands

def main():
    print("\n=== PROFIL SENSORIEL V1 ===\n")

    config = load_config()

    context = {
        "raw": {},
        "validated": {},
        "split": {},
        "errors": [],
        "debug": config.get("debug", False),
        "age_bands" : load_age_bands()
    }

    token = config["tally_token"]

    # 1. FETCH
    print( "1.📥 Récupération des données sur Tally")

    for form_name, form_id in config["forms"].items():

        try:
            raw = fetch_tally(form_id, token)
        except TallyAPIError as e:
            if e.status_code == 401:
                token = replace_tally_token()
                raw = fetch_tally(form_id, token)
            else:
                context["errors"].append(str(e))
                continue

        save_raw_json(raw, form_name)
        context["raw"][form_name] = raw

        print(f"✔ {form_name}")

    if not context["raw"]:
        print("⛔ aucun data")
        return

    # 2. VALIDATE
    print( "\n2.🧹 Validation")
    for form_name, raw in context["raw"].items():
        context["validated"][form_name] = filter_empty_submissions(raw, context)

    # 3. SPLIT
    print( "\n3.✂️ Split")
    for form_name, clean in context["validated"].items():
        context["split"][form_name] = split_dataset(clean, form_name)

    # 4. MAP + SCORE + REPORT
    print("\n4.🧠 Mapping + Scoring + Report")


    reference = json.load(
        open("data/reference/reference.json", encoding="utf-8")
    )

    normes = json.load(
        open("data/reference/normes.json", encoding="utf-8")
    )

    for form_name, submissions in context["split"].items():

        form_ref = reference.get(form_name)

        if not form_ref:
            print(f"\n⚠ référence absente : {form_name}")
            continue

        for submission in submissions:

            submission_id = submission["metadata"]["submission_id"]

            mapped = map_submission(
                submission,
                form_ref["questions"],
                context=context
            )

            patient = mapped["patient"]

            mapped["patient"] = enrich_patient(
                patient,
                form_name,
                context["age_bands"]
            )

            all_scores = compute_all_scores(
                {submission_id: mapped},
                normes,
                form_name
            )

            scores = all_scores[submission_id]

            report = build_final_report(
                mapped,
                scores,
                submission_id
            )

            export_report(
                report,
                mapped["patient"]
            )

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
