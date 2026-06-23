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

from config.settings import load_config, replace_tally_token
from utils.logger import log
from ingestion.fetch_tally import fetch_tally, TallyAPIError
from storage.io_utils import save_raw_json, save_mapped_json, save_scored_json
from pipeline.validate import filter_empty_submissions
from pipeline.split import split_dataset
from pipeline.mapping import (
    map_all_submissions,
)
from pipeline.scoring import compute_scores



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

        print(f"✔ {form_name}: {len(raw.get('submissions', []))} submission(s)")

        print(f"{form_name}: À jour")

    if not context["raw"]:
        print("\n⛔ Aucun formulaire récupéré.")
        return

    # =========================================================
    # 2. VALIDATION
    # =========================================================
    log(context, "\n2.🧹 Validation")

    for form_name, raw in context["raw"].items():
        clean = filter_empty_submissions(raw, context)
        context["validated"][form_name] = clean
        # print(f"{form_name}: Données filtrées")
        print(f"✔ {form_name}: {len(clean['submissions'])} submission(s) valides")

    #    print("\n==========  DEBUG  ==============")

    # for r in clean["submissions"][0]["responses"]:
    # pprint(r)

    # =========================================================
    # 2.5 PROFILING
    # =========================================================
    # log(context, "\n2.5 🔎 Profiling")
    #
    # for form_name, clean in context["validated"].items():
    #    profile_dataset(clean, form_name)
    #    print("\n==========  /DEBUG  ==============")

    # =========================================================
    # 3. SPLIT
    # =========================================================
    log(context, "\n3.✂️ Split")

    for form_name, clean in context["validated"].items():
        submissions = split_dataset(clean)
        context["split"][form_name] = submissions
        print(f"\n✔ {form_name}: {len(submissions)} submission(s) structurées\n")
        # print(f"{form_name}: Éléments séparés")

    # debug léger sur 1 élément
    # if context["split"].get("scolaire"):
    #    print("\n🔎 Exemple split (scolaire):")
    #    pprint(context["split"]["scolaire"][0])

    # =========================================================
    # 4. MAPPING
    # =========================================================
    log(context, "\n4.🧠 Mapping")

    reference = json.load(open("data/reference/reference.json", encoding="utf-8"))

    for form_name, submissions in context["split"].items():
        if not submissions:
            print(f"📭 {form_name}: aucune submission")
            continue

        form_reference = reference.get(form_name)

        # reference_form = reference[form_name]["questions"]

        if not form_reference:
            print(f"⚠️ {form_name}: pas de référence trouvée")
            continue

        mapped = map_all_submissions(
            submissions, reference[form_name]["questions"], context=context
        )

        context["mapped"][form_name] = mapped
        save_mapped_json(data=mapped, form_name=form_name)

        #print(f"\n✔ {form_name}: {len(mapped)} submission(s) mappées")
        #pprint(mapped)  # full

    # =========================================================
    # 5. SCORING
    # =========================================================
    log(context, "\n5.📊 Scoring")

    context = compute_scores(context)
    scored = context["scores"][form_name]
    save_scored_json(data=scored, form_name=form_name)


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

    pprint("\nSCORES :")
    pprint(context["scores"])

    # =========================================================
    # FIN
    # =========================================================
    print("\n=== PIPELINE TERMINÉ ===")

    print("\n📊 Résumé:")
    for form_name in context["mapped"]:
        print(f"- {form_name}: {len(context['mapped'][form_name])}")

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
