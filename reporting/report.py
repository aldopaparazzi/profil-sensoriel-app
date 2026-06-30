import json
from pprint import pprint
from pathlib import Path
from datetime import datetime
from reporting.generate_html import generate_html_report  # Nouvel import

"""
Export du résultat final de scoring vers report.json et HTML.

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

def slugify(text: str) -> str:
    return (
        text.lower()
        .replace(" ", "_")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
    )

def build_report_filename(patient: dict, extension="json") -> str:
    """Construit le nom de fichier avec l'extension appropriée."""
    nom = slugify(patient.get("nom", "unknown"))
    prenom = slugify(patient.get("prenom", "unknown"))
    form_type = patient.get("form_name") or patient.get("form_type") or "unknown"
    date = patient.get("submitted_at") or patient.get("evaluation_date") or "unknown"
    date = safe_date(date)
    return f"{nom}_{prenom}_{form_type}_{date}.{extension}"

def safe_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", ""))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return "unknown_date"

def export_report(report: dict, patient: dict, output_dir="data/report", generate_html=True):
    """
    Exporte le rapport en JSON et optionnellement en HTML.
    
    Args:
        report: dict contenant le rapport complet
        patient: dict contenant les infos patient
        output_dir: dossier de sortie
        generate_html: bool - si True, génère aussi le HTML
    """
    # Export JSON
    json_path = _export_json(report, patient, output_dir)
    
    # Export HTML (optionnel)
    html_path = None
    if generate_html:
        html_path = _export_html(report, patient, output_dir)
    
    return {
        "json": json_path,
        "html": html_path
    }

def _export_json(report: dict, patient: dict, output_dir: str) -> Path:
    """Sauvegarde le rapport en JSON."""
    filename = build_report_filename(patient, "json")
    path = Path(output_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), 
        encoding="utf-8"
    )
    
    print(f"✓ JSON exported: {path}")
    return path

def _export_html(report: dict, patient: dict, output_dir: str) -> Path:
    """Sauvegarde le rapport en HTML."""
    # Charger la référence
    reference_path = Path("data/reference/reference.json")
    if not reference_path.exists():
        print(f"⚠️ Référence non trouvée: {reference_path}")
        return None
    
    with open(reference_path, "r", encoding="utf-8") as f:
        reference = json.load(f)
    
    # Construire le filename HTML
    filename = build_report_filename(patient, "html")
    output_path = Path(output_dir) / "html" / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Générer le HTML
    try:
        html_path = generate_html_report(report, reference, output_path)
        print(f"✓ HTML exported: {html_path}")
        return html_path
    except Exception as e:
        print(f"✗ Erreur génération HTML: {e}")
        return None

def build_final_report(mapped_submission: dict, scores: dict, submission_id: str):
    """Construit la structure finale du rapport."""
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