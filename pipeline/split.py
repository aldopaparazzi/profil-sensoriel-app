# pipeline/split.py

#  ✔ séparation claire
#       patient
#       sensoriel
#       metadata
#  ✔ modèle stable
#       question_id normalisé
#       score isolé
#       submission_id conservé
#  ✔ prêt pour mapping

def split_dataset(clean: dict) -> dict:

    result = []

    for sub in clean.get("submissions", []):

        entry = {
            "metadata_patient": extract_patient_info(sub),
            "sensory_responses": [],
            "comments": [],
            "metadata_techniques": {
                "submission_id": sub.get("id"),
                "submitted_at": sub.get("submittedAt"),
                "form_id": sub.get("formId")
            }
        }

        # =====================================================
        # RESPONSES
        # =====================================================
        for r in sub.get("responses", []):

            answer = r.get("answer")
            qid = r.get("questionId")

            if isinstance(answer, dict):

                for question_id, score in answer.items():
                    entry["sensory_responses"].append({
                        "question_id": str(question_id),
                        "score": score
                    })

            else:
                if answer is not None:
                    entry["comments"].append({
                        "question_id": qid,
                        "text": answer
                    })

        result.append(entry)

    return result

def extract_patient_info(sub: dict) -> dict:

    responses = sub.get("responses", [])

    patient = {
        "prenom": None,
        "nom": None,
        "date_naissance": None,
        "sexe": None,
        "classe": None
    }

    for r in responses:
        qid = r.get("questionId")
        answer = r.get("answer")

        # TODO: mapping à ajuster selon ton référentiel réel
        if qid == "prenom":
            patient["prenom"] = answer
        elif qid == "nom":
            patient["nom"] = answer
        elif qid == "date_naissance":
            patient["date_naissance"] = answer
        elif qid == "sexe":
            patient["sexe"] = answer
        elif qid == "classe":
            patient["classe"] = answer

    return patient