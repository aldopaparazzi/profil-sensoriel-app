from collections import defaultdict
import math


# =========================================================
# 1. UTILITAIRE : IMPUTATION DES ZÉROS
# =========================================================

def clean_values(values):
    """
    Remplace les 0 par la moyenne des valeurs non nulles.
    Règle métier :
    - 0 = valeur manquante (exceptionnelle)
    - imputation globale par moyenne du groupe
    """

    non_zero = [v for v in values if v != 0]

    # sécurité (cas théorique si tout est à 0)
    if not non_zero:
        return values

    mean = sum(non_zero) / len(non_zero)

    return [v if v != 0 else mean for v in values]


# =========================================================
# 2. AGRÉGATION GÉNÉRIQUE
# =========================================================

def aggregate_group(items, key):
    """
    Groupe les scores par clé (domain / quadrant / composante)
    et retourne une liste de valeurs propres.
    """

    groups = defaultdict(list)

    for item in items:
        group = item.get(key)
        score = item.get("score")

        # ignore items sans groupe ou sans score
        if group is None or score is None:
            continue

        groups[group].append(score)

    return groups


def compute_group_scores(groups):
    """
    Applique :
    - imputation des 0
    - somme
    """

    result = {}

    for group, values in groups.items():
        cleaned = clean_values(values)

        result[group] = {
            "raw_score": sum(cleaned),
            "item_count": len(cleaned),
            "mean_score": sum(cleaned) / len(cleaned) if cleaned else None,
        }

    return result


# =========================================================
# 3. NORMALISATION (Z-SCORE)
# =========================================================

def z_score(raw, mean, std):
    """
    Z = (X - μ) / σ
    """

    if std == 0 or std is None:
        return None

    return (raw - mean) / std


def get_age_column(age, age_list):
    """
    Équivalent Excel :
    EQUIV(age; age_list; 1)

    => prend la valeur <= âge la plus proche
    """

    valid = [a for a in age_list if a <= age]

    if not valid:
        return 0

    return age_list.index(max(valid))


# =========================================================
# 4. SCORING PRINCIPAL
# =========================================================

def compute_scores(mapped_submission, reference):
    """
    ENTRY POINT du scoring
    """

    items = mapped_submission["items"]
    form_type = mapped_submission["metadata"].get("form_id")
    age = mapped_submission["patient"].get("age")
    if age is None:
        print("Age manquant dans patient")

    # -----------------------------------------------------
    # 1. AGRÉGATION PAR DIMENSIONS
    # -----------------------------------------------------

    domains = compute_group_scores(
        aggregate_group(items, "domaine_sensoriel")
    )

    quadrants = compute_group_scores(
        aggregate_group(items, "quadrant")
    )

    components = compute_group_scores(
        aggregate_group(items, "composante_scolaire")
    )

    # -----------------------------------------------------
    # 2. TABLES DE RÉFÉRENCE
    # -----------------------------------------------------
    from pprint import pprint
    pprint(reference)

    config = reference["domaines_sensoriels"][form_type]
    config = reference

    age_list = reference["age"]

    age_idx = get_age_column(age, age_list)

    # -----------------------------------------------------
    # 3. NORMALISATION DOMAINE / QUADRANT / COMPOSANTE
    # -----------------------------------------------------

    def enrich_with_zscores(group_scores, table_name):
        enriched = {}

        for name, data in group_scores.items():

            ref = reference["questions"][name]

            mean = ref["m"][age_idx]
            std = ref["sigma"][age_idx]

            enriched[name] = {
                **data,
                "z_score": z_score(data["raw_score"], mean, std),
                "ref_mean": mean,
                "ref_std": std,
            }

        return enriched

    # domaines
    domain_scores = enrich_with_zscores(domains, "domaines")

    # quadrants
    quadrant_scores = enrich_with_zscores(quadrants, "quadrants")

    # composantes scolaires
    component_scores = enrich_with_zscores(components, "composantes")

    # -----------------------------------------------------
    # 4. OUTPUT FINAL
    # -----------------------------------------------------

    return {
        "domains": domain_scores,
        "quadrants": quadrant_scores,
        "composantes": component_scores,
    }