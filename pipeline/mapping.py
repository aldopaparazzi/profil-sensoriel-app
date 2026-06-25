# pipeline\mapping.py
from core.age import resolve_age_group

"""
PIPELINE - MAPPING (ÉTAPE 4)

Objectif :
- enrichir les réponses avec la référence
- ne jamais perdre de données
- tracer toutes les incohérences
- préparer une structure stable pour scoring
"""

# =========================================================
# 1. MAPPING DES RÉPONSES SENSORIELLES
# =========================================================

def map_sensory_responses(responses, reference, context=None):
    """
    Enrichit chaque réponse avec les métadonnées de référence.

    Règle fondamentale :
    - aucune réponse n'est supprimée
    - toute erreur est tracée
    """

    enriched = []
    errors = []
    #print(reference.keys())
    #print(list(reference.values())[0].keys())
    questions_ref = reference #.get("questions", {})

    for response in responses:

        question_id = response.get("question_id")
        score = response.get("score")

        # -------------------------
        # question_id obligatoire
        # -------------------------
        if question_id is None:
            errors.append({
                "type": "missing_question_id",
                "data": response
            })
            continue

        question_id = str(question_id)

        # -------------------------
        # score obligatoire
        # -------------------------
        if score is None:
            errors.append({
                "type": "missing_score",
                "question_id": question_id
            })
            continue

        meta = questions_ref.get(question_id)

        # -------------------------
        # question inconnue
        # -------------------------
        if meta is None:
            errors.append({
                "type": "unknown_question_id",
                "question_id": question_id
            })

            enriched.append({
                "question_id": question_id,
                "score": score,
                #"label": None,
                "quadrant": None,
                "domaine_sensoriel": None,
                "composante_scolaire": None,
                "pour_calcul": False,
                "valid": False
            })
            continue

        # -------------------------
        # mapping normal
        # -------------------------
        enriched.append({
            "question_id": question_id,
            "score": score,
            #"label": meta.get("label"),
            "quadrant": meta.get("quadrant"),
            "domaine_sensoriel": meta.get("domaine_sensoriel"),
            "composante_scolaire": meta.get("composante_scolaire"),
            "pour_calcul": meta.get("pour_calcul", False),
            "valid": True
        })

    # -------------------------
    # remontée des erreurs
    # -------------------------
    if context is not None:
        context.setdefault("mapping_errors", [])
        context["mapping_errors"].extend(errors)

    return enriched


# =========================================================
# 2. MAPPING D'UNE SUBMISSION
# =========================================================

def map_submission(submission, reference, context=None):
    """
    Transforme une submission splitée en submission enrichie.
    """
#    print("TYPE SUBMISSION:", type(submission))
#    print("CONTENT:", submission)
#    patient = submission.get("patient", {})


    if not isinstance(submission, dict):
        raise TypeError(
            f"map_submission attend un dict, reçu: {type(submission)}"
        )
    
    patient = normalize_patient(
        submission.get("patient", {}), 
        submission.get("metadata", {}))

    return {
        "responses": map_sensory_responses(
            submission.get("sensory_responses", []),
            reference,
            context=context
        ),
        "comments": submission.get("comments", {}),
        "patient": patient,
        "respondent": submission.get("respondent", {}),
        "metadata": submission.get("metadata", {})
    }


# =========================================================
# 3. MAPPING MULTI-SUBMISSIONS
# =========================================================

def map_all_submissions(submissions, reference, context=None):
    """
    Applique le mapping à toutes les submissions d'un formulaire.
    """

    mapped = {}

    for submission in submissions:

        mapped_submission = map_submission(
            submission,
            reference,
            context
        )

        submission_id = (
            mapped_submission["metadata"]
            ["submission_id"]
        )

        mapped[submission_id] = mapped_submission

    return mapped


def normalize_patient(patient: dict, metadata: dict) -> dict:
    return {
        "nom": patient.get("Nom"),
        "prenom": patient.get("Prenom"),
        "birth_date": patient.get("Date_naissance"),
        "age_months": patient.get("age"),
        "sexe": patient.get("Sexe"),
        "niveau": patient.get("Niveau"),
        "form_type": metadata.get("form_name"),
        "evaluation_date": metadata.get("submitted_at"),
    }

def enrich_patient(patient, form_name, age_bands):
    age_months = patient.get("age_months")

    patient["age"] = round(age_months / 12, 2) if age_months else None

    patient["age_group"] = resolve_age_group(
        age_months,
        form_name,
        age_bands
    )

    return patient