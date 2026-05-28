# D:\Documents\@Papiers\Elo\PM\Profil sensoriel\app\.vscode\project\pipeline\map.py
import pandas as pd
from pathlib import Path
from config import REFERENCE_DIR, DEBUG_DIR


def load_reference(form_type: str) -> pd.DataFrame:
    """
    Charge la table de référence métier.

    Exemple :
    - enfant.csv
    - jeune_enfant.csv
    - scolaire.csv
    """

    path = REFERENCE_DIR / f"{form_type}.csv"

    if not path.exists():
        raise FileNotFoundError(f"Référence introuvable : {path}")

    ref = pd.read_csv(
        path,
        sep=";",
        encoding="utf-8"
    )

    # harmonisation types
    ref["question_id"] = ref["question_id"].astype(str)

    return ref


def map_questions(
    responses: pd.DataFrame,
    form_type: str,
    debug: bool = False
):
    """
    Extrait uniquement les vraies réponses utiles :

    question_id | response

    Exemple :

    34 -> 5

    Supprime :
    - labels
    - N/A
    - checkbox
    - colonnes parasites
    """

    df = responses.copy()

    # =========================================================
    # passage wide -> long
    # =========================================================

    df = df.melt(
        var_name="question_id",
        value_name="response"
    )

    # =========================================================
    # garder UNIQUEMENT :
    # colonnes numériques
    # =========================================================

    df["question_id"] = df["question_id"].astype(str)

    df = df[
        df["question_id"].str.match(r"^\d+$", na=False)
    ]

    # =========================================================
    # suppression réponses vides
    # =========================================================

    df = df.dropna(subset=["response"])

    # =========================================================
    # chargement référence métier
    # =========================================================

    ref = load_reference(form_type)

    # =========================================================
    # merge métier
    # =========================================================

    df = df.merge(
        ref,
        on="question_id",
        how="left"
    )

    # =========================================================
    # DEBUG
    # =========================================================

    if debug:

        DEBUG_DIR.mkdir(parents=True, exist_ok=True)

        debug_path = DEBUG_DIR / f"{form_type}_mapped.csv"

        df.to_csv(
            debug_path,
            index=False,
            encoding="utf-8"
        )

        print(f"[DEBUG] mapped → {debug_path}")

    return df