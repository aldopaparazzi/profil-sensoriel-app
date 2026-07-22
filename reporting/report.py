# reporting/report.py
from reporting.export import export_all

def build_final_report(mapped_submission: dict, scores: dict, submission_id: str) -> dict:
    """
    Construit la structure finale du rapport.
    """
    patient = mapped_submission["patient"]
    age_months = patient.get("age_months")
    patient = {
        **patient,
        "age": round(age_months / 12, 2) if age_months is not None else None,
    }
    
    mapped = {
        r["question_id"]: r["score"]
        for r in mapped_submission["responses"]
    }
    
    return {
        "submission_id": submission_id,
        "patient": patient,
        "domains": scores.get("domains", {}),
        "quadrants": scores.get("quadrants", {}),
        "composantes_scolaires": scores.get("composantes_scolaires", {}),
        "responses": mapped,
        "comments": mapped_submission.get("comments", {}),
    }

# Pour garder la compatibilité avec l'existant
def export_report(report: dict, patient: dict, generate_html: bool = True, generate_odt: bool = True) -> dict:
    """Alias pour export_all."""
    return export_all(report, patient, generate_html, generate_odt)