# pipeline/split.py
from datetime import datetime
from dateutil import parser
from pprint import pprint
"""
Responsabilité :
    Transformer le JSON Tally validé
    en structure métier normalisée.

Ne fait PAS :
    - de validation métier
    - de calcul
    - de mapping CSV
    - d'enrichissement

Sortie cible :
{
    "patient": {
        "Patient_Prenom": "mon prénom",
        "Patient_Nom": "mon nom",
        "Patient_Sexe": "Fille"
    },

    "respondent": {
        "Repondant_Nom": "troufiniou",
        "Repondant_Profession": "maton"
    },

    "sensory_responses": [
        {"question_id": "1", "score": 1},
        {"question_id": "2", "score": 2},
        ...
    ],

    "comments": [
        {
            "domaine": "Auditif",
            "commentaire": "Il a mal aux oreilles"
        }
    ],

    "metadata": {
        "submission_id": "jex1RA1",
        "form_id": "Me7JAg",
        "respondent_id": "Y59DeQ6",
        "submitted_at": "2026-06-17T14:56:11.000Z",
        "is_completed": True
    }
}
"""

COMMENT_KEYS = {
    "Auditif",
    "Visuel",
    "Tactile",
    "Mouvement",
    "Position_corps",
    "Oral",
    "Comportemental",
    "Conduites",
    "Socio-émotionnel",
    "Attentionnel",
    "Global_Scolaire",
    "Traitement_Global"
}


def split_dataset(clean: dict) -> list:

    result = []

    for sub in clean.get("submissions", []):

        entry = {
            "patient": {},
            "respondent": {},
            "sensory_responses": [],
            "comments": [],
            "metadata": {
                "submission_id": sub.get("id"),
                "form_id": sub.get("formId"),
                "respondent_id": sub.get("respondentId"),
                "submitted_at": sub.get("submittedAt"),
                "is_completed": sub.get("isCompleted")
            }
        }
        birth_date = entry["patient"].get("Patient_DateNaissance")
        submission_date = entry["metadata"].get("submitted_at")

        entry["patient"]["age"] = compute_age(birth_date, submission_date)

        for response in sub.get("responses", []):

            answer = response.get("answer")

            # --------------------------------------
            # dictionnaires
            # --------------------------------------

            if isinstance(answer, dict):

                for key, value in answer.items():

                    # ==============================
                    # Patient
                    # ==============================

                    if key.startswith("Patient_"):
                        clean_key = key.replace("Patient_", "").lower()
                        entry["patient"][clean_key] = value

#                        entry["patient"][key] = value
                        continue

                    # ==============================
                    # Répondant
                    # ==============================

                    if key.startswith("Repondant_"):

                        entry["respondent"][key] = value
                        continue

                    # ==============================
                    # Réponse sensorielle
                    # ==============================

                    if key.isdigit():

                        entry["sensory_responses"].append({
                            "question_id": key,
                            "score": value
                        })

                        continue

                    # ==============================
                    # Commentaire domaine
                    # ==============================

                    if key in COMMENT_KEYS:

                        if value:

                            entry["comments"].append({
                                "domaine": key,
                                "commentaire": value
                            })

                        continue

        result.append(entry)

    return result

""" 
def compute_age(birth_date: str, submission_date: str):
    if not birth_date or not submission_date:
        return None

    birth = datetime.fromisoformat(birth_date)
    sub = datetime.fromisoformat(submission_date)

    return (sub - birth).days // 365
 """
def compute_age(birth_date: str, submission_date: str):
    if not birth_date or not submission_date:
        return None

    birth = parser.isoparse(birth_date)
    sub = parser.isoparse(submission_date)

    return (sub - birth).days // 365