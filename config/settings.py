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


def is_valid_tally_token(token: str) -> bool:
    """
    Vérifie la forme minimale d'un token Tally.

    Un token ne doit contenir aucun espace ni caractère de contrôle.
    """
    if not token:
        return False

    token = str(token)

    return not any(char.isspace() for char in token)


def get_tally_token():
    """
    Lit le token depuis .env.

    Un token vide ou contenant des espaces / retours à la ligne
    est considéré comme invalide.
    """
    if not paths.env_file.exists():
        return ""

    try:
        content = paths.env_file.read_text(encoding="utf-8")
    except OSError:
        return ""

    if "=" not in content:
        return ""

    token = content.split("=", 1)[1].strip()

    if not is_valid_tally_token(token):
        logger.warning("⚠️ Token Tally local invalide.")
        return ""

    return token


# =========================================================
# SAUVEGARDE TOKEN
# =========================================================


def save_tally_token(token: str):
    """
    Écrit un token Tally valide dans .env.

    Refuse toute valeur contenant des espaces ou caractères
    de retour à la ligne.
    """
    if not is_valid_tally_token(token):
        raise ValueError("Token Tally invalide : espaces ou retours à la ligne.")

    paths.env_file.parent.mkdir(parents=True, exist_ok=True)
    paths.env_file.write_text(
        f"TALLY_TOKEN={token}\n",
        encoding="utf-8",
    )


# =========================================================
# SAUVEGARDE TOKEN DEPUIS LE DASHBOARD
# =========================================================


def sauvegarder_token(nouveau_token: str) -> bool:
    """
    Sauvegarde le token dans .env.
    """
    try:
        save_tally_token(nouveau_token)
        return True
    except (OSError, ValueError):
        return False


# =========================================================
# REMPLACEMENT TOKEN
# =========================================================


def replace_tally_token(request_token=None):
    """
    Demande un nouveau token Tally via le mécanisme fourni.
    """
    if not request_token:
        logger.warning("🔑 Token Tally invalide ou expiré.")
        return None

    token = request_token()

    if not token:
        return None

    if not is_valid_tally_token(token):
        logger.warning("⚠️ Token Tally refusé : format invalide.")
        return None

    save_tally_token(token)

    logger.info("Token Tally sauvegardé dans : %s", paths.env_file)

    return token
