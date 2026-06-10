# config/settings.py

import json
#import os
from pathlib import Path

#from dotenv import load_dotenv


# =========================================================
# FICHIERS DE CONFIGURATION
# =========================================================

CONFIG_PATH = Path(__file__).resolve().parent / "runtime.json"
ENV_FILE = Path(__file__).resolve().parent / ".env"


# =========================================================
# CONFIG JSON
# =========================================================

def load_config():
    """
    Charge runtime.json
    et injecte le token Tally.
    """

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    config["tally_token"] = get_tally_token()

    return config


# =========================================================
# TOKEN TALLY
# =========================================================

def get_tally_token():
    """
    Retourne le token Tally.

    Si le fichier .env n'existe pas,
    demande le token à l'utilisateur
    puis le sauvegarde.
    """

    if not ENV_FILE.exists():

        token = input(
            "🔑 Entrez votre token Tally : "
        ).strip()

        save_tally_token(token)

#    load_dotenv(ENV_FILE, override=True)
#    return os.getenv("TALLY_TOKEN")
    content = ENV_FILE.read_text(
        encoding="utf-8"
    ).strip()

    return content.split("=", 1)[1]

def save_tally_token(token: str):
    """
    Sauvegarde le token dans .env.
    """

    ENV_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    ENV_FILE.write_text(
        f"TALLY_TOKEN={token}\n",
        encoding="utf-8"
    )


def replace_tally_token():
    """
    Demande un nouveau token
    et remplace l'ancien.
    """

    token = input(
        "\n🔑 Token invalide. Nouveau token : "
    ).strip()

    save_tally_token(token)
    load_dotenv(ENV_FILE, override=True)

    return token