import sqlite3

DB_PATH = "../database/sensory.db"


def get_norm(form_type, category, age_group, scale):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT mean, sd
        FROM norms
        WHERE form_type = ?
        AND category = ?
        AND age_group = ?
        AND scale = ?
    """, (form_type, category, age_group, scale))

    result = cursor.fetchone()

    conn.close()

    return result


def compute_z_score(raw_score, mean, sd):

    return (raw_score - mean) / sd


# =========================
# TEST
# =========================

raw_score = 62

norm = get_norm(
    form_type="child",
    category="quadrant",
    age_group=4,
    scale="RE"
)

mean, sd = norm

z_score = compute_z_score(raw_score, mean, sd)

print("Score brut :", raw_score)
print("Moyenne :", mean)
print("Écart-type :", sd)
print("Z-score :", round(z_score, 2))