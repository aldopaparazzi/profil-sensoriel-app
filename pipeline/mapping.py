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

    questions_ref = reference.get("questions", {})

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
                "label": None,
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
            "label": meta.get("label"),
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

    return {
        "items": map_sensory_responses(
            submission.get("sensory_responses", []),
            reference,
            context=context
        ),
        "comments": submission.get("comments", {}),
        "patient": submission.get("patient", {}),
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

    mapped = []

    for submission in submissions:
        mapped.append(
            map_submission(submission, reference, context)
        )

    return mapped