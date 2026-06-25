# reporting/report.py
import json
from pprint import pprint
from pathlib import Path
from datetime import datetime


def generate_dummy_report(context):

    print("6.📄 Report")

    print("\nSCORES :")
    print(context["scores"])

    # TODO: HTML / Word plus tard


def generate_report(scores, patient, output_path):

    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Profil Sensoriel</title>
</head>

<body>

<h1>{patient["prenom"]} {patient["nom"]}</h1>

<script>
const SCORES = {json.dumps(scores, ensure_ascii=False)};
</script>

</body>
</html>
"""

    output_path.write_text(html, encoding="utf-8")


def compute_scores(df, cursor, form_type, age_group, age_decimal):

    result = {
        "age_decimal": age_decimal,
        "age_group": age_group,
        "quadrants": {},
        "domains": {},
        "raw_responses": [],
    }

    # Quadrants fixes
    for q in ["RE", "EV", "SE", "EN"]:
        subset = df[df["quadrant"] == q]
        raw = int(subset["response"].sum())

        norm = get_norm(cursor, form_type, "quadrant", age_group, q)

        if norm:
            mean, sd = norm
            ds = z_score(raw, mean, sd)
        else:
            mean, sd, ds = None, None, None

        result["quadrants"][q] = {"raw": raw, "mean": mean, "sd": sd, "ds": ds}

    # Domains fixes
    domains = df["section_name"].unique()

    for d in domains:
        subset = df[df["section_name"] == d]
        raw = int(subset["response"].sum())

        norm = get_norm(cursor, form_type, "domain", age_group, d)

        if norm:
            mean, sd = norm
            ds = z_score(raw, mean, sd)
        else:
            mean, sd, ds = None, None, None

        result["domains"][d] = {"raw": raw, "mean": mean, "sd": sd, "ds": ds}

    for _, row in df.iterrows():
        result["raw_responses"].append(
            {
                "question_id": str(row["question_id"]),
                "section": str(row["section_name"]),
                "quadrant": str(row["quadrant"]),
                "response": int(row["response"]),
                "label": str(row.get("label", ""))[:80],
            }
        )

    return result


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

    return {
        "submission_id": submission_id,
        "patient": patient,  # 👈 IMPORTANT: utiliser le patient modifié
        "domains": scores.get("domains", {}),
        "quadrants": scores.get("quadrants", {}),
        "composantes_scolaires": scores.get("composantes_scolaires", {}),
        "responses": mapped_submission["responses"],
        "comments": mapped_submission.get("comments", {}),
        #"scoring_meta": {"form_type": patient.get("form_type")},
    }
