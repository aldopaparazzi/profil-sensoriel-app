import sqlite3

DB_PATH = "../database/sensory.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

norms = [

    # =========================
    # ENFANT — QUADRANTS
    # Tableau 3.7
    # =========================

    ("child", "quadrant", 4, "RE", 31.0, 9.3),
    ("child", "quadrant", 4, "EV", 33.5, 11.2),
    ("child", "quadrant", 4, "SE", 28.1, 8.8),
    ("child", "quadrant", 4, "EN", 28.4, 6.4),

    ("child", "quadrant", 5, "RE", 31.3, 9.3),
    ("child", "quadrant", 5, "EV", 36.7, 9.6),
    ("child", "quadrant", 5, "SE", 30.0, 7.8),
    ("child", "quadrant", 5, "EN", 29.6, 5.9),

]

cursor.executemany("""
INSERT INTO norms (
    form_type,
    category,
    age_group,
    scale,
    mean,
    sd
)
VALUES (?, ?, ?, ?, ?, ?)
""", norms)

conn.commit()

print("Normes importées.")

conn.close()