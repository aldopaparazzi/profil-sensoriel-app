# main.py

# raw → split → mapped → scores → report
# 1. Fetch Tally json
# 2. Validation
# 3. Split
# 4. Mapping
# 5. Scoring
# 6. Report

# import json
# from pprint import pprint
# from pathlib import Path

from config.settings import load_config, replace_tally_token
from storage.io_utils import save_raw_json, load_cached_submissions
from storage.last_seen import get_last_seen
from pipeline.validate import filter_empty_submissions
from pipeline.split import split_dataset
from pipeline.mapping import map_submission, enrich_patient
from pipeline.scoring import compute_all_scores  # compute_domain_scores
from reporting.report import build_final_report, export_report
from core.age import load_age_bands
from utils.json_cache import load_json_cached
from ingestion.fetch_tally import fetch_new_submissions, fetch_all_submissions_with_pagination, TallyAPIError

def main(force_refresh: bool = False, use_cached=True):
    print("\n=== PROFIL SENSORIEL V1 ===\n")

    config = load_config()

    context = {
        "raw": {},
        "validated": {},
        "split": {},
        "errors": [],
        "debug": config.get("debug", False),
        "age_bands": load_age_bands(),
        "generate_html": config.get("generate_html", True),  # Nouveau paramètre
        "generate_odt": config.get("generate_odt", True),  # Nouveau paramètre
    }

    token = config["tally_token"]

    print("1.📥 Récupération des données sur Tally")


    for form_name, form_id in config["forms"].items():
        try:
            if force_refresh:
                # Mode refresh : tout recharger
                print(f"🔄 Refresh forcé pour {form_name}")
                raw = fetch_all_submissions_with_pagination(form_id, token)
                save_raw_json(raw, form_name, full_refresh=True)
                context["raw"][form_name] = raw
                print(f"✔ {form_name} (refresh complet)")
            else:
                # Mode incrémental : uniquement les nouvelles
                last_seen = get_last_seen(form_name)
                after_id = last_seen.get("last_id") if last_seen else None
                
                if after_id:
                    print(f"📥 {form_name}: après ID {after_id[:8]}...")
                    raw = fetch_new_submissions(form_id, token, after_id)
                else:
                    print(f"📥 {form_name}: premier chargement (aucun ID connu)")
                    raw = fetch_all_submissions_with_pagination(form_id, token)
                
                submissions = raw.get("submissions", [])
                
                if submissions:
                    save_raw_json(raw, form_name)
                    context["raw"][form_name] = raw
                    print(f"✔ {form_name} ({len(submissions)} nouvelles)")
                else:
                    print(f"⏭️ {form_name}: aucune nouvelle soumission")
                    # Charger depuis le cache pour le traitement
                    cached = load_cached_submissions(form_name)
                    if cached:
                        context["raw"][form_name] = {"submissions": cached}
                        print(f"   📦 Utilisation du cache ({len(cached)} soumissions)")
                    else:
                        print(f"   ⚠️ Aucune donnée disponible pour {form_name}")

        except TallyAPIError as e:
            if e.status_code == 401:
                print("🔑 Token invalide ou expiré.")
                success = False
                max_attempts = 3
                attempts = 0
                
                while not success and attempts < max_attempts:
                    token = replace_tally_token()
                    if token is None:
                        print("❌ Aucun token fourni. Abandon pour ce formulaire.")
                        context["errors"].append(f"Token manquant pour {form_name}")
                        break
                    
                    attempts += 1
                    try:
                        raw = fetch_all_submissions_with_pagination(form_id, token)
                        save_raw_json(raw, form_name, full_refresh=True)
                        context["raw"][form_name] = raw
                        print(f"✔ {form_name} (après renouvellement token)")
                        success = True
                    except TallyAPIError as e2:
                        if e2.status_code == 401:
                            print(f"❌ Token toujours invalide (tentative {attempts}/{max_attempts}).")
                        else:
                            context["errors"].append(str(e2))
                            print(f"✗ Erreur pour {form_name}: {e2}")
                            break
                
                if not success and attempts >= max_attempts:
                    print(f"⛔ Abandon après {max_attempts} tentatives pour {form_name}.")
                    context["errors"].append(f"Échec authentification {form_name} après {max_attempts} tentatives")
            else:
                context["errors"].append(str(e))
                print(f"✗ Erreur pour {form_name}: {e}")
    if not context["raw"]:
        print("⛔ aucun data à traiter")
        return


    # 2. VALIDATE
    print("\n2.🧹 Validation")
    for form_name, raw in context["raw"].items():
        context["validated"][form_name] = filter_empty_submissions(raw, context)

    # 3. SPLIT
    print("\n3.✂️ Split")
    for form_name, clean in context["validated"].items():
        context["split"][form_name] = split_dataset(clean, form_name)

    # 4. MAP + SCORE + REPORT
    print("\n4.🧠 Mapping + Scoring + Report")

    '''
    reference = json.load(open("data/reference/reference.json", encoding="utf-8"))
    normes = json.load(open("data/reference/normes.json", encoding="utf-8"))
    '''
    reference = load_json_cached("data/reference/reference.json")
    normes = load_json_cached("data/reference/normes.json")

    for form_name, submissions in context["split"].items():
        form_ref = reference.get(form_name)

        if not form_ref:
            print(f"\n⚠ référence absente : {form_name}")
            continue

        for submission in submissions:
            submission_id = submission["metadata"]["submission_id"]

            mapped = map_submission(submission, form_ref["questions"], context=context)

            patient = mapped["patient"]

            mapped["patient"] = enrich_patient(patient, form_name, context["age_bands"])

            all_scores = compute_all_scores({submission_id: mapped}, normes, form_name)

            scores = all_scores[submission_id]

            report = build_final_report(mapped, scores, submission_id)

            # Export avec génération HTML optionnelle
            export_report(
                report,
                mapped["patient"],
                generate_html=context.get("generate_html", True),
                generate_odt=context.get("generate_odt", True),
            )

    print("\n=== DONE ===")
    return len(submissions)


if __name__ == "__main__":
    import sys
    force_refresh = "--refresh" in sys.argv or "-r" in sys.argv
    main(force_refresh=force_refresh)

def import_forms(force_refresh: bool = False,):
    n = main(force_refresh)
    return n
