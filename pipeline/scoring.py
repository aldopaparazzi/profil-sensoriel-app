"""
PIPELINE - SCORING (ÉTAPE 5)

Objectif :
- calculer les scores bruts
- aucune interprétation clinique
- aucune utilisation des normes
- aucune modification des données source

Entrée :
context["mapped"]

Sortie :
context["scores"]
"""

from collections import defaultdict


# =========================================================
# HELPERS
# =========================================================

def _sum_by_key(items, field_name, use_pour_calcul=False):
    """
    Additionne les scores par catégorie.

    Args:
        items: liste des items mappés
        field_name: quadrant, domaine_sensoriel...
        use_pour_calcul:
            False -> ignore pour_calcul
            True  -> exige pour_calcul == True

    Returns:
        dict
    """

    scores = defaultdict(int)

    for item in items:

        if not item.get("valid", False):
            continue

        if use_pour_calcul and not item.get("pour_calcul", False):
            continue

        key = item.get(field_name)

        if not key:
            continue

        scores[key] += item.get("score", 0)

    return dict(scores)


# =========================================================
# QUADRANTS
# =========================================================

def score_quadrants(items):
    """
    Toutes les questions valides participent.
    """

    return _sum_by_key(
        items,
        "quadrant",
        use_pour_calcul=False
    )


# =========================================================
# DOMAINES SENSORIELS
# =========================================================

def score_domaines_sensoriels(items):
    """
    Seulement les questions :
    - valid == True
    - pour_calcul == True
    """

    return _sum_by_key(
        items,
        "domaine_sensoriel",
        use_pour_calcul=True
    )


# =========================================================
# COMPOSANTES SCOLAIRES
# =========================================================

def score_composantes_scolaires(items):
    """
    Toutes les questions valides participent.
    """

    return _sum_by_key(
        items,
        "composante_scolaire",
        use_pour_calcul=False
    )


# =========================================================
# SCORING D'UNE SUBMISSION
# =========================================================

def score_submission(submission):
    """
    Calcule tous les scores d'une submission.
    """

    items = submission.get("items", [])

    return {
        "quadrants": score_quadrants(items),
        "domaines_sensoriels": score_domaines_sensoriels(items),
        "composantes_scolaires": score_composantes_scolaires(items)
    }


# =========================================================
# SCORING D'UN FORMULAIRE
# =========================================================

def score_form(mapped_form):
    """
    mapped_form :

    {
        "submission_id": {...},
        ...
    }
    """

    results = {}

    for submission_id, submission in mapped_form.items():

        results[submission_id] = score_submission(
            submission
        )

    return results


# =========================================================
# POINT D'ENTRÉE PIPELINE
# =========================================================

def compute_scores(context):
    """
    Remplit context["scores"].

    Structure finale :

    context["scores"] = {
        "scolaire": {
            "submission_id": {...}
        },
        "maison": {...},
        "clinique": {...}
    }
    """

    context.setdefault("scores", {})

    for form_name, mapped_form in context["mapped"].items():

        context["scores"][form_name] = score_form(
            mapped_form
        )

        print(
            f"📊 {form_name}: "
            f"{len(context['scores'][form_name])} score(s)"
        )

    return context