# pipeline\split.py

from utils.age import get_patient_age
from utils.logger import get_logger
from utils.privacy import anonymize_patient

logger = get_logger(__name__)

# =========================================================
# DOMAINES COMMENTAIRES VALIDES
# =========================================================
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
    "Traitement_Global",
}


# =========================================================
# SPLIT PRINCIPAL
# =========================================================
def split_dataset(clean: dict, form_name: str):
    result = []

    submissions = clean.get("submissions", [])
    logger.debug("Split (%d submissions)", len(submissions))

    for sub in submissions:
        metadata = {
            "submission_id": sub.get("id"),
            "form_id": sub.get("formId"),
            "respondent_id": sub.get("respondentId"),
            "submitted_at": sub.get("submittedAt"),
            "is_completed": sub.get("isCompleted"),
            "form_name": form_name,
        }

        patient = {}
        respondent = {}
        sensory_responses = []
        comments = {}
        ignored_fields = []
        form_name = metadata["form_name"]

        # -------------------------------------------------
        # parcours responses
        # -------------------------------------------------
        for response in sub.get("responses", []):
            answer = response.get("answer")

            if not isinstance(answer, dict):
                continue

            for key, value in answer.items():
                # -------------------------
                # PATIENT
                # -------------------------
                if key.startswith("Patient_"):
                    clean_key = key.replace("Patient_", "")
                    patient[clean_key] = value

                # -------------------------
                # REPONDANT
                # -------------------------
                elif key.startswith("Repondant_"):
                    respondent[key] = value

                # -------------------------
                # QUESTIONS
                # -------------------------
                elif str(key).isdigit():
                    sensory_responses.append({"question_id": str(key), "score": value})

                # -------------------------
                # COMMENTAIRES
                # -------------------------
                elif key in COMMENT_KEYS and value:
                    if key in comments:
                        logger.warning(
                            "Commentaire dupliqué (submission %s) : %s",
                            metadata["submission_id"],
                            key,
                        )
                    comments[key] = value

                # -------------------------
                # INCONNU (debug uniquement)
                # -------------------------
                else:
                    ignored_fields.append(key)

        # -------------------------------------------------
        # AGE (sans hypothèse externe)
        # -------------------------------------------------
        patient["age"] = get_patient_age(patient, metadata)

        # -------------------------------------------------
        # LOGS ANONYMISÉS
        # -------------------------------------------------
        logger.info(
            "Traitement %s — submission %s",
            anonymize_patient(patient),
            metadata["submission_id"],
        )
        logger.debug(
            "  patient: %d champs, questions: %d, commentaires: %d",
            len(patient),
            len(sensory_responses),
            len(comments),
        )
        if ignored_fields:
            logger.debug(
                "  champs ignorés (%d): %s",
                len(set(ignored_fields)),
                sorted(set(ignored_fields)),
            )
        # Le nom complet reste accessible en debug uniquement, si besoin ponctuel :
        # logger.debug("Nom complet : %s %s", patient.get("Nom"), patient.get("Prenom"))

        # -------------------------------------------------
        # OUTPUT
        # -------------------------------------------------
        result.append({
            "metadata": metadata,
            "patient": patient,
            "respondent": respondent,
            "sensory_responses": sensory_responses,
            "comments": comments,
        })

    return result
