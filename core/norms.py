# core/norms.py
from pipeline.types import NormResult
import unicodedata

def resolve_norm(
    norms: dict,
    population: str,
    metric_type: str,
    metric_name: str | None,
    age_group: str | None
):
    normalize_key(metric_name)
    
    result: dict[str, float | str | None] = {
        "m": None,
        "sigma": None,
        "age_group_used": None,
        "warning": None,
        "error": None,
    }

    # -----------------------------
    # 1. NAVIGATION SAFE
    # -----------------------------
    pop_data = norms.get(population)
    if not pop_data:
        return {**result, "error": "missing_population"}

    age_block = pop_data.get(age_group)
    if not age_block:
        return {**result, "error": "missing_age_group"}

    # -----------------------------
    # 2. MAPPING DES TYPES
    # -----------------------------
    type_map = {
        "quadrants": "quadrants",
        "domaines_sensoriels": "domaines_sensoriels",
        "composantes_scolaires": "composantes_scolaires"
    }

    norm_key = type_map.get(metric_type)

    if not norm_key:
        return {**result, "error": "unknown_metric_type"}

    metric_table = age_block.get(norm_key)

    if not metric_table:
        return {**result, "error": "missing_metric_type"}

    norm = metric_table.get(metric_name)

    if not norm:
        return {**result, "error": "missing_metric_name"}

    result["m"] = norm.get("m")
    result["sigma"] = norm.get("sigma")
    result["age_group_used"] = age_group

    '''
    print("\nPOP:", population)
    print("AGE_GROUP:", age_group)
    print("AVAILABLE KEYS:", pop_data.keys())
    print("TYPE MAP RESULT:", norm_key)
    print("METRIC TABLE KEYS:", age_block.keys())
    '''
    return result

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
