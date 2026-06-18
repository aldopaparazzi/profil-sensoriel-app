import csv
import json
from pathlib import Path


def convert_csv_to_json(csv_path: str, json_path: str):
    """
    Convertit un CSV de référence en JSON structuré.
    """

    questions = {}

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:
            row = {k.strip(): v for k, v in row.items()}

            qid = row.get("question_id")
            if not qid:
                continue

            questions[str(qid)] = {
                "label": row.get("label"),
                "quadrant": row.get("quadrant"),
                "domaine_sensoriel": row.get("domaine_sensoriel"),
                "composante_scolaire": row.get("composante_scolaire"),
                "pour_calcul": row.get("pour_calcul", "").lower() == "true",
            }

    output = {
        "questions": questions
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✔ JSON généré : {json_path}")


if __name__ == "__main__":
    # 👉 adapte ces chemins si besoin
    csv_file = "data/reference/jeune_enfant.csv"
    json_file = "data/reference/jeune_enfant.json"

    convert_csv_to_json(csv_file, json_file)