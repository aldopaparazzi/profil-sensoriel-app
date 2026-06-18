from dateutil import parser
from pprint import pprint


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
    "Traitement_Global"
}


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


# =========================================================
# SPLIT PRINCIPAL
# =========================================================
def split_dataset(clean: dict):
    result = []

    submissions = clean.get("submissions", [])
    #print(f"\n3.✂️ Split ({len(submissions)} submissions)")

    for sub in submissions:

        metadata = {
            "submission_id": sub.get("id"),
            "form_id": sub.get("formId"),
            "respondent_id": sub.get("respondentId"),
            "submitted_at": sub.get("submittedAt"),
            "is_completed": sub.get("isCompleted"),
        }

        patient = {}
        respondent = {}
        sensory_responses = []
        comments = {}
        ignored_fields = []

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
                    sensory_responses.append({
                        "question_id": str(key),
                        "score": value
                    })

                # -------------------------
                # COMMENTAIRES
                # -------------------------
                elif key in COMMENT_KEYS and value:
                    if key in comments:
                        print(
                            f"⚠️ commentaire dupliqué "
                            f"({metadata['submission_id']}) : {key}"
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
        patient["age"] = compute_age(
            patient.get("Date_naissance"),
            metadata.get("submitted_at")
        )

        # -------------------------------------------------
        # LOGS PROPRES
        # -------------------------------------------------
        print(f"   └── {metadata['submission_id']}")
        print(f"       ├── patient: {len(patient)} champs")
        print(f"       ├── questions: {len(sensory_responses)}")
        print(f"       ├── commentaires: {len(comments)}")
        if ignored_fields:
            print(f"       ├── ignorés: {len(set(ignored_fields))}")
            pprint(ignored_fields)

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