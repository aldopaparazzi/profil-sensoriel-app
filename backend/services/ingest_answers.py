from pathlib import Path
import sqlite3
import pandas as pd
from config import DB_PATH, RAW_DIR

def get_latest_csv(form_type: str, base_dir: Path):
    raw_dir = base_dir / "data/raw"

    latest = raw_dir / f"{form_type}_latest.csv"

    if latest.exists():
        return latest

    raise FileNotFoundError("No latest file found")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = (BASE_DIR / "../../database/sensory.db").resolve()
CSV_PATH = get_latest_csv("enfant", BASE_DIR)

print("DB:", DB_PATH)
print("CSV:", CSV_PATH)

conn = sqlite3.connect(DB_PATH)
df = pd.read_csv(RAW_DIR / "enfant_2026-05-26_15-45-16.csv")
cursor = conn.cursor()

for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO answers (
            form_id,
            question_code,
            quadrant,
            component,
            section_name,
            answer_value
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        1,  # temporaire patient/form id
        row.get("question_code", None),
        row.get("quadrant", None),
        row.get("component", None),
        row.get("section_name", None),
        row.get("response", 0)
    ))

conn.commit()
conn.close()