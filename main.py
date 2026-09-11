# main.py

"""
- **Description**: Ce script est le point d'entrée principal de l'application Profil Sensoriel. Il gère la récupération, la validation, le traitement et la génération des rapports pour les soumissions de données.
- **Fonctionnalités principales**:
  - Récupération des données depuis Tally.
  - Validation des données pour supprimer les soumissions vides.
  - Séparation des données en différents groupes selon certaines critères.
  - Mapping et scoring des données pour calculer les indicateurs de santé.
  - Génération de rapports HTML et ODT basés sur les résultats du scoring.
- **Paramètres**:
  - `force_refresh`: Option pour forcer la récupération complète des données, plutôt que d'utiliser le mode incrémental.
  - `request_token`: Token d'authentification optionnel pour accéder aux données de Tally.
- **Utilisation**: Ce script est appelé directement depuis la ligne de commande et peut être lancé avec l'option `--refresh` ou `-r` pour forcer une mise à jour complète des données. Les résultats sont exportés dans des fichiers HTML et ODT selon les configurations du script.

"""

from config.settings import load_config, replace_tally_token
from core.age import load_age_bands
from ingestion.fetch_tally import (
    TallyAPIError,
    fetch_all_submissions_with_pagination,
    fetch_new_submissions,
)
from pipeline.mapping import enrich_patient, map_submission
from pipeline.scoring import compute_all_scores  # compute_domain_scores
from pipeline.split import split_dataset
from pipeline.validate import filter_empty_submissions
from reporting.report import build_final_report, export_report
from storage.io_utils import load_cached_submissions, save_raw_json
from storage.last_seen import get_last_seen
from storage.paths import paths
from utils.json_cache import load_json_cached
from utils.logger import configure_logging, get_logger

logger = get_logger(__name__)


def main(force_refresh: bool = False, request_token=None, use_cached=True):
    config = load_config()
    configure_logging(config.get("debug", False))

    logger.info("=== PROFIL SENSORIEL V1.5 ===", extra={"status": True})

    context = {
        "raw": {},
        "validated": {},
        "split": {},
        "errors": [],
        "debug": config.get("debug", False),
        "age_bands": load_age_bands(),
        "generate_html": config.get("generate_html", True),
        "generate_odt": config.get("generate_odt", True),
    }

    token = config["tally_token"]

    logger.info("1. 📥 Récupération des données sur Tally", extra={"status": True})

    for form_name, form_id in config["forms"].items():
        try:
            if force_refresh:
                # Mode refresh : tout recharger
                logger.info("🔄 Refresh forcé pour %s", form_name)
                raw = fetch_all_submissions_with_pagination(form_id, token)
                save_raw_json(raw, form_name, full_refresh=True)
                context["raw"][form_name] = raw
                logger.info("✔ %s (refresh complet)", form_name)
            else:
                # Mode incrémental : uniquement les nouvelles
                last_seen = get_last_seen(form_name)
                after_id = last_seen.get("last_id") if last_seen else None

                if after_id:
                    logger.info("📥 %s: après ID %s...", form_name, after_id[:8])
                    raw = fetch_new_submissions(form_id, token, after_id)
                else:
                    logger.info("📥 %s: premier chargement (aucun ID connu)", form_name)
                    raw = fetch_all_submissions_with_pagination(form_id, token)

                submissions = raw.get("submissions", [])

                if submissions:
                    save_raw_json(raw, form_name)
                    context["raw"][form_name] = raw
                    logger.info("✔ %s (%d nouvelles)", form_name, len(submissions))
                else:
                    logger.info("⏭️ %s: aucune nouvelle soumission", form_name)
                    # Charger depuis le cache pour le traitement
                    cached = load_cached_submissions(form_name)
                    if cached:
                        context["raw"][form_name] = {"submissions": cached}
                        logger.info(
                            "📦 Utilisation du cache (%d soumissions)", len(cached)
                        )
                    else:
                        logger.info("⚠️ Aucune donnée disponible pour %s", form_name)

        except TallyAPIError as e:
            if e.status_code == 401:
                logger.warning("🔑 Token invalide ou expiré.")
                success = False
                max_attempts = 3
                attempts = 0

                while not success and attempts < max_attempts:
                    token = replace_tally_token(request_token)
                    if token is None:
                        logger.error(
                            "❌ Aucun token fourni. Abandon pour ce formulaire."
                        )
                        context["errors"].append(f"Token manquant pour {form_name}")
                        break

                    attempts += 1
                    try:
                        raw = fetch_all_submissions_with_pagination(form_id, token)
                        save_raw_json(raw, form_name, full_refresh=True)
                        context["raw"][form_name] = raw
                        logger.info("✔ %s (après renouvellement token)", form_name)
                        success = True
                    except TallyAPIError as e2:
                        if e2.status_code == 401:
                            logger.warning(
                                "❌ Token toujours invalide (tentative %d/%d).",
                                attempts,
                                max_attempts,
                            )
                        else:
                            context["errors"].append(str(e2))
                            logger.error("✗ Erreur pour %s: %s", form_name, e2)
                            break

                if not success and attempts >= max_attempts:
                    logger.error(
                        "⛔ Abandon après %d tentatives pour %s.",
                        max_attempts,
                        form_name,
                    )
                    context["errors"].append(
                        f"Échec authentification {form_name} après {max_attempts} tentatives"
                    )
            else:
                context["errors"].append(str(e))
                logger.error("✗ Erreur pour %s: %s", form_name, e)

    if not context["raw"]:
        logger.warning("⛔ aucun data à traiter")
        return

    # 2. VALIDATE
    logger.info("2. 🧹 Validation", extra={"status": True})
    for form_name, raw in context["raw"].items():
        context["validated"][form_name] = filter_empty_submissions(raw, context)

    for form_name, validated in context["validated"].items():
        submissions = validated.get("submissions", [])
        logger.info(
            "🔎 VALIDATED %s : %d soumissions",
            form_name,
            len(submissions),
        )

    # 3. SPLIT

    logger.info("3. ✂️ Split", extra={"status": True})
    for form_name, clean in context["validated"].items():
        result = split_dataset(clean, form_name)
        context["split"][form_name] = result

        logger.info(
            "🔎 SPLIT %s : %d éléments",
            form_name,
            len(result) if result else 0,
        )

    # 4. MAP + SCORE + REPORT
    logger.info("4. 🧠 Mapping + Scoring + Report", extra={"status": True})

    reference = load_json_cached(paths.reference_path)
    normes = load_json_cached(paths.normes_path)

    exported_count = 0

    logger.info(
        "🔎 Contenu de context['split'] : %s",
        {k: len(v) if v else 0 for k, v in context["split"].items()},
    )

    logger.info("========== DEBUG AVANT EXPORT ==========")

    for form_name, submissions in context["split"].items():
        logger.info(
            "FORMULAIRE : %s | TYPE=%s | NB=%s",
            form_name,
            type(submissions).__name__,
            len(submissions) if hasattr(submissions, "__len__") else "?",
        )
        """
        if submissions:
            logger.info(
                "PREMIER ELEMENT : %r",
                submissions[0] if isinstance(submissions, list) else submissions,
            )
        """
    logger.info("========================================")

    for form_name, submissions in context["split"].items():
        form_ref = reference.get(form_name)

        if not form_ref:
            logger.warning("⚠ référence absente : %s", form_name)
            continue

        for submission in submissions:
            submission_id = submission["metadata"]["submission_id"]

            mapped = map_submission(
                submission,
                form_ref["questions"],
                context=context,
            )

            patient = mapped["patient"]
            mapped["patient"] = enrich_patient(
                patient,
                form_name,
                context["age_bands"],
            )

            all_scores = compute_all_scores(
                {submission_id: mapped},
                normes,
                form_name,
            )

            scores = all_scores[submission_id]

            report = build_final_report(
                mapped,
                scores,
                submission_id,
            )

            export_report(
                report,
                mapped["patient"],
                generate_html=context.get("generate_html", True),
                generate_odt=context.get("generate_odt", True),
            )

            exported_count += 1

    logger.info("=== DONE ===", extra={"status": True})
    logger.info("Exported %d patients", exported_count)

    return exported_count


if __name__ == "__main__":
    import sys

    force_refresh = "--refresh" in sys.argv or "-r" in sys.argv
    main(force_refresh=force_refresh)


def import_forms(
    force_refresh: bool = False,
    request_token=None,
):
    return main(
        force_refresh=force_refresh,
        request_token=request_token,
    )

