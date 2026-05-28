import pandas as pd
import logging
from typing import Dict, Optional

from config.sources import GOOGLE_SHEETS
from storage.io_utils import save_raw_csv

logger = logging.getLogger(__name__)


# =========================
# LOAD SINGLE DATASET
# =========================

def load_data(url: str) -> Optional[pd.DataFrame]:
    """
    Charge un CSV depuis une URL Google Sheets / endpoint CSV
    """

    try:
        df = pd.read_csv(url)

        if df is None or df.empty:
            logger.warning("Fichier vide")
            return None

        return df

    except Exception as e:
        logger.error(f"Erreur lecture CSV : {e}")
        return None


# =========================
# IMPORT PIPELINE
# =========================

def run_import() -> Dict[str, pd.DataFrame]:
    """
    Charge tous les formulaires définis dans GOOGLE_SHEETS
    + snapshot RAW si changement détecté
    """

    datasets = {}

    for form_name, config in GOOGLE_SHEETS.items():

        logger.info(f"=== Import : {form_name} ===")

        df = load_data(config["url"])

        if df is None:
            logger.warning(f"Skip : {form_name}")
            continue

        # 🔥 snapshot RAW + détection changement
        path = save_raw_csv(df, form_name)

        if path:
            logger.info(f"RAW saved : {path}")
        else:
            logger.info(f"No change detected : {form_name}")

        datasets[form_name] = df

    logger.info(f"Import terminé | datasets={len(datasets)}")

    return datasets

def run():
    dfs = {}

    for form_name, config in GOOGLE_SHEETS.items():
        print(f"=== {form_name} ===")

        df = load_data(config["url"])
        if df is None:
            continue

        path = save_raw_csv(df, form_name)
        dfs[form_name] = df

    return dfs