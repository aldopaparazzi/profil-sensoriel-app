# config/settings.py

import json
from pathlib import Path

# =========================================================
# CHEMINS
# =========================================================

CONFIG_PATH = Path(__file__).resolve().parent / "runtime.json"
ENV_FILE = Path(__file__).resolve().parent / ".env"


# =========================================================
# CONFIG PRINCIPALE
# =========================================================

def load_config():
    """
    Charge runtime.json et injecte le token Tally.
    """

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    config["tally_token"] = get_tally_token()

    return config


# =========================================================
# TOKEN MANAGEMENT
# =========================================================

def get_tally_token():
    """
    Lit le token depuis .env.

    Règles :
    - si .env n'existe pas → demande utilisateur
    - si fichier invalide → erreur explicite
    """

    # -----------------------------------------------------
    # CAS 1 : fichier absent → création interactive
    # -----------------------------------------------------
    if not ENV_FILE.exists():
        token = input("🔑 Entrez votre token Tally : ").strip()
        save_tally_token(token)
        return token

    # -----------------------------------------------------
    # CAS 2 : lecture fichier existant
    # -----------------------------------------------------
    content = ENV_FILE.read_text(encoding="utf-8").strip()

    # sécurité minimale
    if "=" not in content:
        raise ValueError("Fichier .env invalide (format attendu: TALLY_TOKEN=xxx)")

    return content.split("=", 1)[1]


# =========================================================
# SAUVEGARDE TOKEN
# =========================================================

def save_tally_token(token: str):
    """
    Écrit le token dans .env.

    Remplace entièrement le fichier.
    """

    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)

    ENV_FILE.write_text(
        f"TALLY_TOKEN={token}\n",
        encoding="utf-8"
    )


# =========================================================
# REMPLACEMENT TOKEN (ERREUR 401)
# =========================================================

def replace_tally_token():
    """
    Appelé quand l'API retourne 401.

    Comportement :
    - demande un nouveau token
    - écrase .env
    - retourne le token immédiatement
    """

    token = input("\n🔑 Token invalide. Nouveau token : ").strip()

    save_tally_token(token)

    return token