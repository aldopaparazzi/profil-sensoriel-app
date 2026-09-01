# pipeline/validate.py

"""
Validation et nettoyage des soumissions Tally.

Responsabilité :
    - vérifier la structure minimale d'une soumission ;
    - supprimer les soumissions réellement vides ;
    - conserver la structure Tally d'origine.

Structure attendue :

submission
└── responses
    ├── response
    │   └── answer
    ├── response
    │   └── answer
    └── ...
"""

from typing import Any

from utils.logger import get_logger

logger = get_logger(__name__)


# =========================================================
# VALEURS VIDES
# =========================================================


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


# =========================================================
# REPONSES SIGNIFICATIVES
# =========================================================


def has_meaningful_response(responses: Any) -> bool:
    """
    Vérifie si la liste 'responses' contient au moins
    une réponse réellement renseignée.

    Structure Tally :

        responses = [
            {
                "answer": {
                    "Patient_Nom": "Dupont"
                }
            },
            ...
        ]
    """

    if not isinstance(responses, list):
        return False

    for response in responses:
        if not isinstance(response, dict):
            continue

        answer = response.get("answer")

        if not isinstance(answer, dict):
            continue

        for value in answer.values():
            if not is_empty_value(value):
                return True

    return False


# =========================================================
# VALIDATION PRINCIPALE
# =========================================================


def filter_empty_submissions(
    raw: dict,
    context: dict | None = None,
) -> dict:
    """
    Filtre les soumissions vides tout en conservant
    la structure Tally.

    Une soumission est conservée si 'responses' contient
    au moins une valeur renseignée.
    """

    if not raw:
        raise ValueError("Dataset vide")

    submissions = raw.get("submissions", [])

    if not isinstance(submissions, list):
        raise ValueError("Structure invalide : 'submissions' doit être une liste")

    filtered = []
    empty_count = 0

    for submission in submissions:
        if not isinstance(submission, dict):
            empty_count += 1
            continue

        responses = submission.get("responses", [])

        if not isinstance(responses, list):
            logger.warning(
                "⚠️ Submission %s sans liste 'responses'",
                submission.get("id"),
            )
            empty_count += 1
            continue

        if has_meaningful_response(responses):
            filtered.append(submission)

        else:
            empty_count += 1
            logger.debug(
                "⏭️ Submission vide ignorée : %s",
                submission.get("id"),
            )

    logger.info(
        "Validation : %d conservées / %d reçues / %d vides",
        len(filtered),
        len(submissions),
        empty_count,
    )

    return {
        **raw,
        "submissions": filtered,
    }
