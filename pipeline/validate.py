# pipeline/validate.py

# Responsabilité :
#   vérifier
#   nettoyer
#   garantir la cohérence minimale

from typing import Any

# from utils.logger import get_logger, logger


def is_empty_value(value: Any) -> bool:
    """
    Retourne True si une valeur est considérée comme vide.
    """
    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == ""

    if isinstance(value, (list, tuple, set)):
        return len(value) == 0

    if isinstance(value, dict):
        return len(value) == 0

    return False


def has_meaningful_answer(responses: dict[str, Any]) -> bool:
    """
    Vérifie si au moins une réponse contient une valeur non vide.
    """
    return any(not is_empty_value(value) for value in responses.values())


def filter_empty_submissions(raw: dict, context: dict | None = None) -> dict:
    """
    Filtre les soumissions vides tout en conservant la structure Tally.
    """
    if not raw:
        raise ValueError("Dataset vide")

    submissions = raw.get("submissions", [])

    filtered = []

    for submission in submissions:
        answers = submission.get("answers")

        if not isinstance(answers, dict):
            continue

        if has_meaningful_answer(answers):
            filtered.append(submission)

    return {
        **raw,
        "submissions": filtered,
    }


"""old
def filter_empty_submissions(raw: dict, context: dict) -> dict:
    if not raw:
        raise ValueError("Dataset vide")
    if "submissions" not in raw:
        raise ValueError("Structure invalide: missing submissions")
    cleaned = {"submissions": []}
    for sub in raw["submissions"]:
        if not sub.get("responses"):
            logger.warning("⚠️ submission sans responses :", sub.get("id"))
            continue
        cleaned["submissions"].append(sub)
    return cleaned

"""
