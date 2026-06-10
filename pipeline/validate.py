# pipeline/validate.py

# Responsabilité :
#   vérifier
#   nettoyer
#   garantir la cohérence minimale

import pandas as pd
from utils.logger import log


def validate_dataset(raw: dict, context: dict) -> dict:

    if not raw:
        raise ValueError("Dataset vide")

    if "submissions" not in raw:
        raise ValueError("Structure invalide: missing submissions")

    cleaned = {
        "submissions": []
    }

    for sub in raw["submissions"]:

        if not sub.get("responses"):
            continue

        cleaned["submissions"].append(sub)

    return cleaned

def validate_dataset_pd(df: pd.DataFrame, context: dict | None = None) -> pd.DataFrame:
    if context is None:
        context = {"debug": True}

    log(context, "\n=== VALIDATION ===")

    # =========================================================
    # 0. SAFE CHECK (IMPORTANT)
    # =========================================================
    if df is None:
        log(context, "❌ DataFrame = None")
        return pd.DataFrame()

    if df.empty:
        log(context, "⚠️ DataFrame vide dès l'entrée validation")
        return df

    log(context, "COLUMNS:", list(df.columns))
    log(context, "SHAPE:", df.shape)

    df = df.copy()

    # =========================================================
    # 1. nettoyage colonnes (SAFE)
    # =========================================================
    df.columns = [
        str(c).strip() if c is not None else ""
        for c in df.columns
    ]

    # =========================================================
    # 2. normalisation colonnes critiques
    # =========================================================
    if "submissionId" in df.columns:
        df = df.dropna(subset=["submissionId"])
    else:
        log(context, "⚠️ submissionId absent du dataset")

    # =========================================================
    # 3. suppression doublons
    # =========================================================
    before = len(df)
    df = df.drop_duplicates()
    log(context, f"🧹 doublons supprimés: {before - len(df)}")

    # =========================================================
    # 4. suppression colonnes vides
    # =========================================================
    before_cols = len(df.columns)
    df = df.dropna(axis=1, how="all")
    log(context, f"🧹 colonnes vides supprimées: {before_cols - len(df.columns)}")

    # =========================================================
    # 5. SAFE FINAL CHECK
    # =========================================================
    log(context, "FINAL SHAPE:", df.shape)

    return df
