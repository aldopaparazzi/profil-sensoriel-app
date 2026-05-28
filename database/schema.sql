CREATE TABLE patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    birth_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE forms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,

    form_type TEXT NOT NULL,
    age_band INTEGER NOT NULL,

    source TEXT,
    raw_payload TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(patient_id) REFERENCES patients(id)
);

CREATE TABLE answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    form_id INTEGER NOT NULL,

    question_code TEXT NOT NULL,

    quadrant TEXT,
    component TEXT,
    section_name TEXT,

    answer_value INTEGER,

    FOREIGN KEY(form_id) REFERENCES forms(id)
);

CREATE TABLE scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    form_id INTEGER NOT NULL,

    score_type TEXT NOT NULL,
    score_name TEXT NOT NULL,

    raw_score REAL,
    mean_score REAL,
    std_dev REAL,
    z_score REAL,

    interpretation TEXT,

    FOREIGN KEY(form_id) REFERENCES forms(id)
);

CREATE TABLE norms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    form_type TEXT NOT NULL,

    category_type TEXT NOT NULL,

    category_name TEXT NOT NULL,

    age_band INTEGER NOT NULL,

    mean_score REAL NOT NULL,
    std_dev REAL NOT NULL
);