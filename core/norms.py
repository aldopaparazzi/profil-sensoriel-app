# core/norms.py
# from pipeline.types import NormResult
# from pprint import pprint
import unicodedata


def resolve_norm(norms, population, metric_type, metric_name, age_group):
    metric_name = normalize_key(metric_name)

    result = {
        "m": None,
        "sigma": None,
        "age_group_used": None,
        "warning": None,
        "error": None,
    }

    # -----------------------------
    # 1. CHECK POPULATION
    # -----------------------------
    pop_data = norms.get(population)
    if pop_data is None:
        return {**result, "error": "missing_population"}

    # -----------------------------
    # 2. CHECK AGE GROUP
    # -----------------------------
    age_block = pop_data.get(age_group)
    if age_block is None:
        return {**result, "error": "missing_age_group"}

    # -----------------------------
    # 3. VERROU MÉTIER (IMPORTANT)
    # -----------------------------
    forbidden = {"jeune_enfant", "enfant"}

    if metric_type == "composantes_scolaires" and population in forbidden:
        return {
            **result,
            "error": "not_allowed_for_population",
            "warning": f"{metric_type} interdit pour {population}",
        }

    # -----------------------------
    # 4. CHOIX DU BLOC
    # -----------------------------
    metric_table = age_block.get(metric_type)

    if metric_table is None:
        return {**result, "error": "missing_metric_type"}

    # -----------------------------
    # 5. CHOIX DE LA MESURE
    # -----------------------------
    norm = metric_table.get(metric_name)

    if norm is None:
        return {**result, "error": "missing_metric_name"}

    # -----------------------------
    # 6. RESULTAT
    # -----------------------------
    return {
        **result,
        "m": norm.get("m"),
        "sigma": norm.get("sigma"),
        "age_group_used": age_group,
    }


def normalize_key(value: str | None) -> str | None:
    """
    Normalise toutes les clés métier pour éviter les mismatch :
    - casse
    - accents
    - espaces
    - tirets
    """

    if value is None:
        return None

    value = str(value).strip().lower()

    # suppression accents
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))

    # standardisation séparateurs
    value = value.replace(" ", "_").replace("-", "_")

    return value
