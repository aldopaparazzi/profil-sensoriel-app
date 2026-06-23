# pipeline\scoring.py

from typing import TypedDict, Optional
from pipeline.types import NormResult

# =========================================================
# SCORING - DOMAINES SENSORIELS (Z-SCORE)
# =========================================================

def compute_domain_scores(mapped_submissions, normes, form_name):

    results = {}

    for submission_id, submission in mapped_submissions.items():

        items = submission.get("items", [])
        patient = submission.get("patient", {})

        age_group = patient.get("age")

        domain_scores = {}

        for item in items:

            if not item.get("pour_calcul"):
                continue

            domain = item["domaine_sensoriel"]
            raw = item["score"]

            norm = resolve_norm(
                norms=normes,
                population=form_name,
                metric_type="domaines_sensoriels",
                metric_name=domain,
                age_group=str(age_group) if age_group else None
            )

            if norm["error"]:
                domain_scores[domain] = {
                    "raw": raw,
                    "z": None,
                    "error": norm["error"]
                }
                continue

            m = norm["m"]
            sigma = norm["sigma"]

            z = (raw - m) / sigma if sigma else None

            domain_scores[domain] = {
                "raw": raw,
                "z": z,
                "warning": norm["warning"]
            }

        results[submission_id] = domain_scores

    return results

def compute_z_score(raw, m, sigma):
    """
    z = (raw - m) / sigma
    """

    if sigma == 0:
        return None

    return round((raw - m) / sigma, 2)

def resolve_norm(
    norms: dict,
    population: str,
    metric_type: str,
    metric_name: str,
    age_group: str | None
) -> NormResult:

    result: NormResult = {
        "m": None,
        "sigma": None,
        "age_group_used": None,
        "warning": None,
        "error": None,
    }

    # =========================================================
    # 1. population
    # =========================================================
    pop_data = norms.get(population)
    if not pop_data:
        result["error"] = "missing_population"
        return result

    # =========================================================
    # 2. age group
    # =========================================================
    if not age_group:
        result["error"] = "missing_age_group"
        return result

    age_block = pop_data.get(age_group)
    if not age_block:
        result["error"] = "missing_age_group"
        return result

    # =========================================================
    # 3. metric type
    # =========================================================
    metric_table = age_block.get(metric_type)
    if not metric_table:
        result["error"] = "missing_metric_type"
        return result

    # =========================================================
    # 4. metric name
    # =========================================================
    norm = metric_table.get(metric_name)
    if not norm:
        result["error"] = "missing_metric_name"
        return result

    # =========================================================
    # 5. extraction
    # =========================================================
    result["m"] = norm["m"]
    result["sigma"] = norm["sigma"]
    result["age_group_used"] = age_group

    return result
