# core\age.py
from dateutil import parser
import json
from functools import lru_cache

@lru_cache(maxsize=1)
def load_age_bands():
    with open("data/reference/ages.json", "r", encoding="utf-8") as f:
        return json.load(f)
# =========================================================
# AGE (optionnel, tolérant)
# =========================================================
def compute_age(birth_date, submission_date):
    if not birth_date or not submission_date:
        return None

    try:
        birth = parser.isoparse(str(birth_date)).replace(tzinfo=None)
        sub = parser.isoparse(str(submission_date)).replace(tzinfo=None)
        return (sub - birth).days // 365
    except Exception:
        return None

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
        '''
        print("\nAGE DEBUG:", age_years, form_name)
        print("age:", age_years)
        print("form:", form_name)
        print("AVAILABLE BANDS:", bands)
        '''
    return bands[0]["key"] if age_years < bands[0]["min"] else bands[-1]["key"]


def age_to_group(age, population, age_bands):
    if age is None:
        return None

    config = age_bands.get(population)
    if not config:
        return None

    for band in config["bands"]:
        if band["min"] <= age <= band["max"]:
            return band["key"]

    return None

if __name__ == "__main__":
    print(compute_age("2018-01-01", "2020-01-01"))
