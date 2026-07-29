# config/settings.py

import json
from pathlib import Path

from config import paths

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
    except Exception:
        return False


# =========================================================
# REMPLACEMENT TOKEN (ERREUR 401)
# =========================================================


def replace_tally_token():
    """
    Appelé quand l'API retourne 401 (mode CLI uniquement).

    Comportement :
    - demande un nouveau token
    - possibilité d'abandonner (laisser vide)
    - écrase .env
    - retourne le token ou None si abandon
    """

    print("\n🔑 Token Tally invalide ou expiré.")
    print("   (Laissez vide pour abandonner)")
    token = input("   Nouveau token : ").strip()

    if not token:
        print("❌ Abandon demandé.")
        return None

    save_tally_token(token)
    print("✅ Token sauvegardé.")
    return token
