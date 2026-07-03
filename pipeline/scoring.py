# pipeline\scoring.py
from core.age import resolve_age_group, load_age_bands
from core.norms import resolve_norm, normalize_key
from core.scoring_math import compute_z_score


def compute_all_scores(mapped_submissions, normes, form_name):
    """
    Calcule tous les scores pour toutes les submissions d'un formulaire.
    """
    age_bands = load_age_bands()
    results = {}
    
    for submission_id, submission in mapped_submissions.items():
        patient = submission["patient"]
        items = submission["responses"]

        # Calcul des scores bruts par domaine
        domain_raw = {}
        quadrant_raw = {}
        comp_raw = {}
        
        for item in items:
            score = item.get("score", 0)
            
            if item.get("pour_calcul", False):
                domain = item.get("domaine_sensoriel")
                if domain:
                    domain_raw[domain] = domain_raw.get(domain, 0) + score
            
            quadrant = item.get("quadrant")
            if quadrant:
                quadrant_raw[quadrant] = quadrant_raw.get(quadrant, 0) + score
            
            comp = item.get("composante_scolaire")
            if comp:
                comp_raw[comp] = comp_raw.get(comp, 0) + score
        
        age_months = patient["age_months"]
        age_group = resolve_age_group(age_months, form_name, age_bands)

        results[submission_id] = {
            "patient": {**patient, "age_decimal": age_months, "age_group": age_group},
            "domains": _compute_scores_for_type(
                domain_raw, normes, form_name, age_group, "domaines_sensoriels"
            ),
            "quadrants": _compute_scores_for_type(
                quadrant_raw, normes, form_name, age_group, "quadrants"
            ),
            "composantes_scolaires": _compute_scores_for_type(
                comp_raw, normes, form_name, age_group, "composantes_scolaires"
            ),
        }

    return results


def _compute_scores_for_type(raw_scores, normes, form_name, age_group, metric_type):
    """Fonction interne pour calculer les scores d'un type de métrique."""
    results = {}

    for key, raw in raw_scores.items():
        normalized_key = normalize_key(key)
        norm = resolve_norm(normes, form_name, metric_type, normalized_key, age_group)

        if norm.get("error"):
            results[key] = {
                "raw": raw,
                "mean": None,
                "sigma": None,
                "z": None,
                "error": norm["error"],
            }
        else:
            mean = norm["m"]
            sigma = norm["sigma"]
            results[key] = {
                "raw": raw,
                "mean": mean,
                "sigma": sigma,
                "z": compute_z_score(raw, mean, sigma),
            }

    return results
