from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parents[2] / "database" / "sensory.db"

def compute_quadrant_scores(form_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            quadrant,
            SUM(answer_value) as raw_score
        FROM answers
        WHERE form_id = ?
        GROUP BY quadrant
    """, (form_id,))

    results = cursor.fetchall()
    conn.close()

    return {q: s for q, s in results}


if __name__ == "__main__":
    print(compute_quadrant_scores(1))