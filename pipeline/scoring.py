# pipeline/scoring.py

def compute_scores(context):

    print("5.📊 Scoring")

    df = context["mapped"]

    # TODO: vrais calculs
    context["scores"] = {
        "RE": 0,
        "EV": 0,
        "SE": 0,
        "EN": 0
    }

    return context


# =========================
# =========================
# OLD SCRIPT FOR REFERENCE
# =========================
# =========================
from typing import Dict, Any
import pandas as pd
from pprint import pprint

# =========================
# debug
# =========================
def print_results(results: dict):
    print("\n=== SCORES QUADRANTS ===\n")

    for quadrant, data in results.items():
        print(f"{quadrant}")
        print(f"  raw   : {data['raw']}")
        print(f"  mean  : {data['mean']}")
        print(f"  sd    : {data['sd']}")
        print(f"  z     : {data['z']}")
        print(f"  class : {data['class']}")
        print("")


# =========================================================
# 1. IMPUTATION DES VALEURS
# =========================================================

def impute_missing_by_category_mean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remplace les réponses invalides (0 ou NaN selon ton modèle)
    par la moyenne du quadrant correspondant.

    Hypothèse métier :
    - 0 = item non applicable
    - donc imputé par moyenne du groupe
    """

    df = df.copy()

    # On considère 0 comme "non applicable"
    df["response"] = df["response"].replace(0, pd.NA)

    # moyenne par quadrant
    mean_by_quadrant = df.groupby("quadrant")["response"].transform("mean")

    # remplacement des NA par la moyenne du groupe
    df["response"] = df["response"].fillna(mean_by_quadrant)

    return df


# =========================================================
# 2. SCORE BRUT PAR QUADRANT
# =========================================================

def compute_raw_scores(df: pd.DataFrame) -> Dict[str, float]:
    """
    Somme des réponses par quadrant.

    Exemple :
        RE -> 62
        EV -> 38
        SE -> 31
        EN -> 47
    """

    return df.groupby("quadrant")["response"].sum().to_dict()


# =========================================================
# 3. Z-SCORE
# =========================================================

def compute_z_score(raw: float, mean: float, sd: float) -> float:
    """
    Normalisation statistique standard :

        z = (x - μ) / σ
    """

    if sd == 0:
        return 0.0  # sécurité minimale

    return (raw - mean) / sd


# =========================================================
# 4. CLASSIFICATION CLINIQUE
# =========================================================

def classify_z_score(z: float) -> str:
    """
    Classification standard type psychométrie.

    Ajustable avec la psychomotricienne ensuite.
    """

    if z <= -2:
        return "Très inférieur"
    if z <= -1:
        return "Inférieur"
    if z < 1:
        return "Dans la norme"
    if z < 2:
        return "Supérieur"
    return "Très supérieur"


# =========================================================
# 5. RÉCUPÉRATION DES NORMES
# =========================================================

def get_norm(norm_table: Dict[str, Any], form_type: str, variable: str, age: int):
    """
    Accès aux tables de normes en mémoire.

    norm_table structure attendue :
    {
        "RE": {
            4: {"mean": 31, "sd": 9.3},
            5: {"mean": 32, "sd": 8.7}
        },
        ...
    }

    ⚠️ On suppose ici que l'âge est déjà discrétisé
    (comme dans Excel : 4.88 → 4)
    """

    try:
        return norm_table[form_type][variable][age]
    except KeyError:
        raise ValueError(
            f"Norme introuvable pour {form_type=} {variable=} {age=}"
        )


# =========================================================
# 6. PIPELINE COMPLET QUADRANTS
# =========================================================

def compute_quadrant_scores(
    df: pd.DataFrame,
    norm_table: Dict[str, Any],
    form_type: str,
    age: float
) -> Dict[str, Dict[str, Any]]:
    """
    Pipeline complet :
    1. imputation
    2. score brut
    3. norme
    4. z-score
    5. classification
    """

    # -----------------------------------------------------
    # 1. préparation des données
    # -----------------------------------------------------

    df = impute_missing_by_category_mean(df)

    # -----------------------------------------------------
    # 2. score brut
    # -----------------------------------------------------

    raw_scores = compute_raw_scores(df)

    results = {}

    # -----------------------------------------------------
    # 3. discrétisation âge (Excel-like)
    # -----------------------------------------------------

    age_int = int(age)

    # -----------------------------------------------------
    # 4. calcul par quadrant
    # -----------------------------------------------------

    for quadrant, raw in raw_scores.items():

        norm = get_norm(
            norm_table,
            form_type=form_type,
            variable=quadrant,
            age=age_int
        )

        z = compute_z_score(
            raw,
            norm["mean"],
            norm["sd"]
        )

        results[quadrant] = {
            "raw": float(raw),
            "mean": norm["mean"],
            "sd": norm["sd"],
            "z": round(z, 2),
            "class": classify_z_score(z)
        }

    return results


# =========================================================
# 7. EXEMPLE D'UTILISATION
# =========================================================

if __name__ == "__main__":

    # exemple minimal
    df = pd.DataFrame({
        "quadrant": ["RE", "RE", "EV", "SE", "EN"],
        "response": [5, 4, 3, 2, 4]
    })

    # exemple de normes simplifiées
    norm_table = {
        "scolaire": {
            "RE": {
                4: {"mean": 31, "sd": 9.3}
            },
            "EV": {
                4: {"mean": 33, "sd": 11.2}
            },
            "SE": {
                4: {"mean": 28, "sd": 8.8}
            },
            "EN": {
                4: {"mean": 28, "sd": 6.4}
            }
        }
    }

    results = compute_quadrant_scores(
        df=df,
        norm_table=norm_table,
        form_type="scolaire",
        age=4.88
    )

#    print(results)
    print_results(results)