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
from pipeline.validate import filter_empty_submissions
from pipeline.split import split_dataset
from pipeline.mapping import map_all_submissions #,load_reference, map_sensory_responses
#from pipeline.profiling import profile_dataset
#from pipeline.scoring import compute_scores

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
        #print(f"{form_name}: Données filtrées")
        print(f"✔ {form_name}: {len(clean['submissions'])} submission(s) valides")

#    print("\n==========  DEBUG  ==============")

    # for r in clean["submissions"][0]["responses"]:
    # pprint(r)

    # =========================================================
    # 2.5 PROFILING
    # =========================================================
    #log(context, "\n2.5 🔎 Profiling")
    #
    #for form_name, clean in context["validated"].items():
    #    profile_dataset(clean, form_name)
#    print("\n==========  /DEBUG  ==============")


    # =========================================================
    # 3. SPLIT
    # =========================================================
    log(context, "\n3.✂️ Split")

    for form_name, clean in context["validated"].items():
        submissions = split_dataset(clean)
        context["split"][form_name] = submissions
        print(f"✔ {form_name}: {len(submissions)} submission(s) structurées\n")
        # print(f"{form_name}: Éléments séparés")

    # debug léger sur 1 élément
    #if context["split"].get("scolaire"):
    #    print("\n🔎 Exemple split (scolaire):")
    #    pprint(context["split"]["scolaire"][0])

    # =========================================================
    # 4. MAPPING (IMPORTANT: PAR FORM)
    # =========================================================
    log(context, "\n4.🧠 Mapping")

    # chargement centralisé des références
    references = {
        "enfant": json.load(open("data/reference/enfant.json", encoding="utf-8")),
        "jeune_enfant": json.load(open("data/reference/jeune_enfant.json", encoding="utf-8")),
        "scolaire": json.load(open("data/reference/scolaire.json", encoding="utf-8")),
    }

    for form_name, submissions in context["split"].items():

        if not submissions:
            print(f"📭 {form_name}: aucune submission")
            continue

        reference = references.get(form_name)

        if not reference:
            print(f"⚠️ {form_name}: pas de référence trouvée")
            continue

        mapped = map_all_submissions(
            submissions,
            reference,
            context=context
        )

        context["mapped"][form_name] = mapped

        print(f"✔ {form_name}: {len(mapped)} submission(s) mappées")

    #pprint(context["mapped"]) #full

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
