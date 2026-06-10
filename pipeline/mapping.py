# pipeline/mapping.py

import csv
from pathlib import Path


def map_questions(context):

    print("4.🧠 Mapping")

    df = context["answers"]

    # TODO: merge avec reference CSV
    context["mapped"] = df

    return context

import csv

def load_reference(path: str):

    reference = {}

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:

            row = {k.strip(): v for k, v in row.items()}

            qid = row.get("question_id")

            if not qid:
                continue

            reference[str(qid)] = {
                "label": row.get("label"),
                "quadrant": row.get("quadrant"),
                "domaine_sensoriel": row.get("domaine_sensoriel"),
                "composante_scolaire": row.get("composante_scolaire"),
                "pour_calcul": row.get("pour_calcul", "").lower() == "true"
            }

    return reference

def map_sensory_responses(responses, reference):

    enriched = []

    for r in responses:

        qid = str(r["question_id"])
        score = r["score"]

        meta = reference.get(qid)

        if not meta:
            continue  # ou log error

        enriched.append({
            "question_id": qid,
            "score": score,
            "label": meta["label"],
            "quadrant": meta["quadrant"],
            "domaine_sensoriel": meta["domaine_sensoriel"],
            "composante_scolaire": meta["composante_scolaire"],
            "pour_calcul": meta["pour_calcul"]
        })

    return enriched

def load_reference_by_form(form_name: str):

    path = f"data/reference/{form_name}.csv"

    return load_reference(path)
    