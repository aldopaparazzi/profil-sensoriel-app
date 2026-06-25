# reporting/build_report.py

def build_final_report(patient, mapped, scores):
    submission = next(iter(mapped.values()))

    return {
        "patient": {
            "prenom": patient.get("prenom"),
            "nom": patient.get("nom"),
            "form_type": patient.get("form_type"),
            "birth_date": patient.get("birth_date"),
            "evaluation_date": patient.get("evaluation_date"),
            "age_decimal": patient.get("age_decimal"),
            "age_group": patient.get("age_group"),
        },

        "quadrants": scores.get("quadrants", {}),
        "domains": scores.get("domains", {}),

        "items": {
            r["question_id"]: r["score"]
            for r in submission["sensory_responses"]
        }
    }
    