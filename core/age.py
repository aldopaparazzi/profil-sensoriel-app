# core\age.py

import json
from functools import lru_cache

from storage.paths import paths
from utils.logger import logger


@lru_cache(maxsize=1)
def load_age_bands():
    with paths.ages_path.open(encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# AGE (optionnel, tolérant)
# =========================================================
def resolve_age_group(age_years, form_name, age_bands):
    if age_years is None:
        return None
    config = age_bands.get(form_name)
    bands = config.get("bands", [])
    if not bands:
        return None
    if not config:
        return bands[0]["key"] if bands else None
    for band in bands:
        if band["min"] <= age_years <= band["max"]:
            return band["key"]

        logger.debug(
            "AGE DEBUG: %s years, form: %s, available bands: %s",
            age_years,
            form_name,
            bands,
        )

    return bands[0]["key"] if age_years < bands[0]["min"] else bands[-1]["key"]
