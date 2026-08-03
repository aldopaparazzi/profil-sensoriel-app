# utils/logger.py
"""
Configuration centralisée du logging.

Règle :
    Dans chaque module, utiliser :

        from utils.logger import get_logger
        logger = get_logger(__name__)

    puis logger.info(...) / logger.warning(...) / logger.error(...) / logger.debug(...)
    à la place de print().

Le niveau (DEBUG ou INFO) est piloté par runtime.json ("debug": true/false),
via configure_logging(), appelé une seule fois au tout début de l'application
(main.py pour le CLI, ui.py pour l'appli Qt).
"""

import logging

_CONFIGURED = False


def configure_logging(debug: bool = False) -> None:
    """
    Configure le logging racine. À appeler UNE SEULE FOIS,
    le plus tôt possible dans le programme.

    Appels suivants ignorés (idempotent) pour éviter les
    doublons de handler si plusieurs modules l'appellent.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """
    Retourne un logger nommé.
    Usage recommandé : logger = get_logger(__name__)
    """
    return logging.getLogger(name)


# ----------------------------------------------------------
# Compatibilité avec le code existant (ui.py, storage/init.py
# font déjà `from utils.logger import logger`)
# ----------------------------------------------------------
logger = logging.getLogger("profil_sensoriel")


# ----------------------------------------------------------
# Anciens helpers (context["debug"]) — conservés mais dépréciés.
# Migrer progressivement vers logger.debug() / logger.info().
# ----------------------------------------------------------
def short_log(context, *args):
    if context.get("debug"):
        print(*args)


def log(context, *args, tag=None, level="info"):
    if not context.get("debug") and level == "debug":
        return
    prefix = f"[{tag}]" if tag else ""
    print(prefix, *args)
