#from utils.logger import log

#from pprint import pprint
from utils.age import get_patient_age

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
# SPLIT PRINCIPAL
# =========================================================
def split_dataset(clean: dict, form_name: str):
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
            "form_name": form_name
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
        patient["age"] = get_patient_age(
            patient,
            metadata,
            form_name
        )

        
        # -------------------------------------------------
        # LOGS PROPRES
        # -------------------------------------------------
        print("\n"+patient["Nom"]+" "+patient["Prenom"])
        print(f"   └── {metadata['submission_id']}")
        print(f"       ├── patient: {len(patient)} champs")
        print(f"       ├── questions: {len(sensory_responses)}")
        print(f"       ├── commentaires: {len(comments)}")
        if ignored_fields:
            print(f"       ├── ignorés: {len(set(ignored_fields))}")
#            pprint(ignored_fields)
#        print("\n")
        
        
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