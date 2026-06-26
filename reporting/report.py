# reporting/report.py
import json
from pprint import pprint
from pathlib import Path
from datetime import datetime


"""
Export du résultat final de scoring vers report.json.

Ce module constitue la frontière entre :

    pipeline de calcul
            ↓
        report.json
            ↓
    génération HTML / PDF / DOCX

Le fichier exporté doit respecter strictement le contrat :

{
    "patient": {...},
    "quadrants": {...},
    "domains": {...},
    "responses": {...}
}
"""


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------
'''
def _clean_scores(scores: dict) -> dict:
    """
    Conserve uniquement les informations nécessaires
    pour le reporting.

    Entrée possible :

    {
        "recherche": {
            "raw": 62,
            "z": 3.33,
            "warning": None,
            "extra": ...
        }
    }

    Sortie :

    {
        "recherche": {
            "raw": 62,
            "z": 3.33
        }
    }
    """

    cleaned = {}

    for name, data in scores.items():

        cleaned[name] = {
            "raw": data.get("raw"),
            "z": data.get("z"),
        }

    return cleaned
'''


def slugify(text: str) -> str:
    return (
        text.lower()
        .replace(" ", "_")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
    )


def build_report_filename(patient: dict) -> str:
    nom = slugify(patient.get("nom", "unknown"))
    prenom = slugify(patient.get("prenom", "unknown"))

    form_type = patient.get("form_name") or patient.get("form_type") or "unknown"
    date = patient.get("submitted_at") or patient.get("evaluation_date") or "unknown"
    date = safe_date(date)

    return f"{nom}_{prenom}_{form_type}_{date}.json"


def safe_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", ""))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return "unknown_date"


# ------------------------------------------------------------------
# MAIN EXPORT
# ------------------------------------------------------------------


def export_report(report: dict, patient: dict, output_dir="data/report"):
    filename = build_report_filename(patient)

    path = Path(output_dir) / filename

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✓ Report exported: {path}")
    return path


def build_final_report(mapped_submission: dict, scores: dict, submission_id: str):

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
        "patient": patient,  # 👈 IMPORTANT: utiliser le patient modifié
        "domains": scores.get("domains", {}),
        "quadrants": scores.get("quadrants", {}),
        "composantes_scolaires": scores.get("composantes_scolaires", {}),
        "responses": mapped,
        "comments": mapped_submission.get("comments", {}),
        #"scoring_meta": {"form_type": patient.get("form_type")},
    }
