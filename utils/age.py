# utils/age.py
from dateutil import parser


def compute_age(birth_date, submission_date):
    if not birth_date or not submission_date:
        return None

    try:
        birth = parser.isoparse(str(birth_date)).replace(tzinfo=None)
        sub = parser.isoparse(str(submission_date)).replace(tzinfo=None)
        return (sub - birth).days / 365.25
    except (ValueError, TypeError):
        return None


def age_to_months(age_years: float) -> float:
    return age_years * 12


def get_patient_age(patient: dict, submission: dict):
    """
    Retourne l'âge en MOIS (standard pipeline scoring)
    """

    birth = patient.get("Date_naissance")
    submitted_at = submission.get("submitted_at")
    age_years = compute_age(birth, submitted_at)
    if age_years is None:
        return None
    return age_to_months(age_years)


def age_warning(age, form_name, age_bands):
    if age is None:
        return None

    config = age_bands.get(form_name)
    if not config:
        return "missing_form_config"

    bands = config["bands"]

    if age < bands[0]["min"]:
        return "age_below_range"

    if age > bands[-1]["max"]:
        return "age_above_range"

    return None
