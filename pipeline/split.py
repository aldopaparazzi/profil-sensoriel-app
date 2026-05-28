import pandas as pd
from pathlib import Path


ZERO_MARKER = "zero"

DEBUG_DIR = Path("data/debug")


def split_patient_responses(
    df: pd.DataFrame,
    debug: bool = False,
    name: str = "dataset"
):
    """
    Split dataframe Tally en :

    - patients
    - réponses

    Le marqueur 'zero' sépare :
    [infos patient] | zero | [questions]
    """

    df = df.copy()

    # nettoyage noms colonnes
    df.columns = df.columns.str.strip()

    # sécurité
    if ZERO_MARKER not in df.columns:
        raise ValueError("Marker 'zero' introuvable")

    cols = list(df.columns)

    zero_idx = cols.index(ZERO_MARKER)

    # ---------------------------------------------------------
    # séparation
    # ---------------------------------------------------------

    patient_cols = cols[:zero_idx]

    question_cols = cols[zero_idx + 1:]

    patients = df[patient_cols].copy()

    responses = df[question_cols].copy()

    # ---------------------------------------------------------
    # DEBUG
    # ---------------------------------------------------------

    if debug:

        DEBUG_DIR.mkdir(parents=True, exist_ok=True)

        patients_path = DEBUG_DIR / f"{name}_patients_split.csv"

        responses_path = DEBUG_DIR / f"{name}_responses_split.csv"

        patients.to_csv(
            patients_path,
            index=False,
            encoding="utf-8"
        )

        responses.to_csv(
            responses_path,
            index=False,
            encoding="utf-8"
        )

        print(f"[DEBUG] {name} patients → {patients_path}")

        print(f"[DEBUG] {name} responses → {responses_path}")

    return patients, responses