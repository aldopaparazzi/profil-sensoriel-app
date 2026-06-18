# pipeline/mapping.py

"""
Étape 4 : Mapping

Objectif :
- enrichir chaque réponse sensorielle avec les métadonnées
  provenant du JSON de référence
- ne jamais perdre de question
- détecter les incohérences
- remonter les erreurs dans le contexte
- rester indépendant du chargement des références
  (fait désormais dans main.py)
"""

# =========================================================
# MAPPING D'UNE LISTE DE RÉPONSES SENSORIELLES
# =========================================================

def map_sensory_responses(responses, reference, context=None):
    """
    Transforme :

    {
        "question_id": "12",
        "score": 4
    }

    en :

    {
        "question_id": "12",
        "score": 4,
        "label": "...",
        "quadrant": "...",
        ...
    }

    Une question inconnue est conservée
    mais marquée comme invalide.
    """

    enriched = []
    errors = []

    questions_ref = reference.get("questions", {})

    for response in responses:

        question_id = response.get("question_id")
        score = response.get("score")

        # -------------------------------------------------
        # sécurité : question_id obligatoire
        # -------------------------------------------------
        if question_id is None:

            errors.append({
                "type": "missing_question_id",
                "data": response
            })

            continue

        question_id = str(question_id)

        # -------------------------------------------------
        # sécurité : score obligatoire
        # -------------------------------------------------
        if score is None:

            errors.append({
                "type": "missing_score",
                "question_id": question_id
            })

            continue

        # -------------------------------------------------
        # recherche dans la référence
        # -------------------------------------------------
        meta = questions_ref.get(question_id)

        # -------------------------------------------------
        # question inconnue
        # -------------------------------------------------
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

        # -------------------------------------------------
        # mapping normal
        # -------------------------------------------------
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

    # -------------------------------------------------
    # remontée des erreurs dans le contexte
    # -------------------------------------------------
    if context is not None and errors:

        context.setdefault("mapping_errors", [])
        context["mapping_errors"].extend(errors)

    return enriched


# =========================================================
# MAPPING D'UNE SUBMISSION
# =========================================================

def map_submission(submission, reference, context=None):
    """
    Reçoit une submission issue du split.

    Conserve :
    - patient
    - respondent
    - metadata
    - comments

    Remplace :
    - sensory_responses
      par
    - items enrichis
    """

    mapped_items = map_sensory_responses(
        submission.get("sensory_responses", []),
        reference,
        context=context
    )

    return {
        "items": mapped_items,
        "comments": submission.get("comments", []),
        "patient": submission.get("patient", {}),
        "respondent": submission.get("respondent", {}),
        "metadata": submission.get("metadata", {})
    }


# =========================================================
# MAPPING DE TOUTES LES SUBMISSIONS D'UN FORMULAIRE
# =========================================================

def map_all_submissions(submissions, reference, context=None):
    """
    Reçoit :

    [
        submission_1,
        submission_2,
        ...
    ]

    Retourne :

    [
        mapped_submission_1,
        mapped_submission_2,
        ...
    ]
    """

    mapped_submissions = []

    for submission in submissions:

        mapped_submission = map_submission(
            submission,
            reference,
            context=context
        )

        mapped_submissions.append(mapped_submission)

    return mapped_submissions