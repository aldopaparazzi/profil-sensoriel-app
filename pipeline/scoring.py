# pipeline\scoring.py
from pprint import pprint

from core.age import resolve_age_group, load_age_bands, normalize_age
from core.norms import resolve_norm, normalize_key, normalize_item
from core.scoring_math import compute_z_score


def compute_metric_scores(raw_scores, normes, form_name, age_group, metric_type):

    results = {}

    for key, raw in raw_scores.items():
        key = normalize_key(key)

        norm = resolve_norm(
            norms=normes,
            population=form_name,
            metric_type=metric_type,
            metric_name=key,
            age_group=age_group,
        )

        if norm["error"]:
            results[key] = {
                "raw": raw,
                "mean": None,
                "sigma": None,
                "z": None,
                "error": norm["error"],
            }
            continue

        mean = norm["m"]
        sigma = norm["sigma"]

        results[key] = {
            "raw": raw,
            "mean": mean,
            "sigma": sigma,
            "z": compute_z_score(raw, mean, sigma),
        }

    return results


def compute_raw_scores(items, group_field, only_pour_calcul=False):

    results = {}
    for items in items:
        if only_pour_calcul and not items.get("pour_calcul"):
            continue
        key = items.get(group_field)
        if not key:
            continue
        score = items.get("score", 0)
        results[key] = results.get(key, 0) + score
    return results


def compute_final_scores(raw_scores, normes, form_name, age_group, metric_type):
    results = {}

    for key, raw in raw_scores.items():
        norm = resolve_norm(
            norms=normes,
            population=form_name,
            metric_type=metric_type,
            metric_name=key,
            age_group=age_group,
        )

        if norm["error"]:
            results[key] = {
                "raw": raw,
                "mean": None,
                "sigma": None,
                "z": None,
                "error": norm["error"],
            }
            continue

        mean = norm["m"]
        sigma = norm["sigma"]

        results[key] = {
            "raw": raw,
            "mean": mean,
            "sigma": sigma,
            "z": compute_z_score(raw, mean, sigma),
        }

    return results


def compute_all_scores(mapped_submissions, normes, form_name):

    age_bands = load_age_bands()
    results = {}
    for submission_id, submission in mapped_submissions.items():
        patient = submission["patient"]
        items = submission["responses"]
        items = (
            submission["responses"]["responses"]
            if "responses" in submission and isinstance(submission["responses"], dict)
            else submission["responses"]
        )
        """
        print("\n=== ITEMS DEBUG ===")
        print(type(items))
        pprint(items)
        """
        domain_raw = compute_raw_scores(
            items, "domaine_sensoriel", only_pour_calcul=True
        )
        quadrant_raw = compute_raw_scores(items, "quadrant")
        comp_raw = compute_raw_scores(items, "composante_scolaire")
        age_months = patient["age_months"]
        age_group = resolve_age_group(age_months, form_name, age_bands)
        results[submission_id] = {
            "patient": {**patient, "age_decimal": age_months, "age_group": age_group},
            "domains": compute_final_scores(
                domain_raw, normes, form_name, age_group, "domaines_sensoriels"
            ),
            "quadrants": compute_final_scores(
                quadrant_raw, normes, form_name, age_group, "quadrants"
            ),
            "composantes_scolaires": compute_final_scores(
                comp_raw, normes, form_name, age_group, "composantes_scolaires"
            ),
        }
    '''
    print("AGE MONTHS:", patient["age_months"])
    print("AGE DECIMAL:", age_months)
    print("AGE GROUP:", age_group)
    print("FORM:", form_name)
    '''
    return results
