# pipeline/profiling.py

from collections import Counter


def profile_dataset(raw: dict, form_name: str) -> None:
    """
    Analyse exploratoire du JSON Tally.

    Objectifs :
    - compter les soumissions
    - compter les réponses
    - identifier les types rencontrés
    - inventorier les clés présentes dans les dict
    - préparer la conception du split

    IMPORTANT :
    - ne modifie rien
    - ne retourne rien
    - affichage uniquement
    """

    submissions = raw.get("submissions", [])

    response_count = 0

    answer_types = Counter()
    dict_keys = Counter()

    print(f"\n--- PROFILING : {form_name} ---\n")

    # =========================================================
    # ENVELOPPE TALLY
    # =========================================================

    print("=" * 60)
    print(" MÉTADONNÉES DE SOUMISSION")
    print("=" * 60)

    if submissions:

        sample = submissions[0]

        for key in sample.keys():
            print(key)

    else:
        print("Aucune soumission")

    # =========================================================
    # ANALYSE DES RÉPONSES
    # =========================================================

    for submission in submissions:

        for response in submission.get("responses", []):

            response_count += 1

            answer = response.get("answer")

            answer_type = type(answer).__name__

            answer_types[answer_type] += 1

            if isinstance(answer, dict):

                for key in answer.keys():
                    dict_keys[key] += 1

    # =========================================================
    # SYNTHÈSE
    # =========================================================

    print("\n" + "=" * 60)
    print(" SYNTHÈSE")
    print("=" * 60)

    print(f"Soumissions : {len(submissions)}")
    print(f"Réponses    : {response_count}")

    # =========================================================
    # TYPES
    # =========================================================

    print("\nTypes de réponses :")

    for name, count in sorted(answer_types.items()):
        print(f"  {name:<15} {count}")

    # =========================================================
    # CLÉS DES DICTS
    # =========================================================

    print("\nClés rencontrées dans les dictionnaires :\n")

    for key in sorted(dict_keys.keys()):
        print(f"  {key}")

    # =========================================================
    # CLASSEMENT AUTOMATIQUE
    # =========================================================

    patient_keys = []
    respondent_keys = []
    sensory_keys = []
    comment_keys = []
    other_keys = []

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

    for key in sorted(dict_keys.keys()):

        if key.startswith("Patient_"):
            patient_keys.append(key)

        elif key.startswith("Repondant_"):
            respondent_keys.append(key)

        elif key.isdigit():
            sensory_keys.append(key)

        elif key in COMMENT_KEYS:
            comment_keys.append(key)

        else:
            other_keys.append(key)

    # =========================================================
    # CATÉGORIES
    # =========================================================

    print("\n" + "=" * 60)
    print(" VARIABLES PATIENT")
    print("=" * 60)

    for key in patient_keys:
        print(key)

    print("\n" + "=" * 60)
    print(" VARIABLES RÉPONDANT")
    print("=" * 60)

    for key in respondent_keys:
        print(key)

    print("\n" + "=" * 60)
    print(" DOMAINES DE COMMENTAIRES")
    print("=" * 60)

    for key in comment_keys:
        print(key)

    print("\n" + "=" * 60)
    print(" QUESTIONS SENSORIELLES")
    print("=" * 60)

    if sensory_keys:

        print(
            f"{len(sensory_keys)} question(s) détectée(s)"
        )

        print(
            f"de {min(map(int, sensory_keys))}"
            f" à {max(map(int, sensory_keys))}"
        )

    print("\n" + "=" * 60)
    print(" AUTRES CLÉS")
    print("=" * 60)

    for key in other_keys:
        print(key)

    print()