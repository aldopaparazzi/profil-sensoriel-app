# config/settings.py

import json

from storage.paths import paths
from utils.logger import logger

# =========================================================
# CONFIG PRINCIPALE
# =========================================================


def load_config():
    """
    Charge runtime.json et injecte le token Tally.
    """

    with open(paths.runtime_json, "r", encoding="utf-8") as f:
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
    - si .env n'existe pas → retourne chaîne vide
    - si fichier invalide → retourne chaîne vide
    """

    if not paths.env_file.exists():
        return ""
    content = paths.env_file.read_text(encoding="utf-8").strip()
    if "=" not in content:
        return ""
    return content.split("=", 1)[1]


# =========================================================
# SAUVEGARDE TOKEN
# =========================================================


def save_tally_token(token: str):
    """
    Écrit le token dans .env.
    Remplace entièrement le fichier.
    """
    paths.env_file.parent.mkdir(parents=True, exist_ok=True)
    paths.env_file.write_text(f"TALLY_TOKEN={token}\n", encoding="utf-8")


# =========================================================
# SAUVEGARDE TOKEN (DEPUIS LE DASHBOARD)
# =========================================================


def sauvegarder_token(nouveau_token: str) -> bool:
    """
    Sauvegarde le token dans .env.
    Fonction appelée depuis le dashboard Streamlit.
    Retourne True si succès, False sinon.
    """
    if not nouveau_token or not nouveau_token.strip():
        return False
    try:
        save_tally_token(nouveau_token.strip())
        return True
    except OSError:
        return False


# =========================================================
# REMPLACEMENT TOKEN (ERREUR 401)
# =========================================================


def replace_tally_token(request_token=None):
    """
    Demande un nouveau token Tally via le mécanisme fourni.

    Avec Qt, request_token est un callback qui bloque le worker
    jusqu'à ce que l'UI fournisse le token.
    """

    if not request_token:
        logger.warning("🔑 Token Tally invalide ou expiré.")
        return None

    token = request_token()

    if not token:
        return None

    save_tally_token(token)
    logger.info("Token Tally sauvegardé dans : %s", paths.env_file)

    return token
