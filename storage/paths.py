# storage/paths.py
"""
Gestion centralisée des chemins de l'application Profil Sensoriel.

Architecture :

Application (lecture seule)
│
├── config/
│   └── runtime.json
│
├── data/
│   └── reference/
│       ├── reference.json
│       ├── normes.json
│       ├── ages.json
│       ├── template.html
│       └── template.odt
│
├── reporting/
│   └── code de génération des rapports
│
└── favicon_io/
    └── favicon.png


Données utilisateur (lecture / écriture)
│
└── Documents/
    └── Profil Sensoriel/
        ├── .env
        ├── Raw/
        │   ├── .state.json
        │   └── .last_seen.json
        │
        └── Rapports/
            ├── json/
            ├── html/
            └── bilan/


Convention :

APP_DIR
    Dossier contenant l'application ou l'exécutable.

RESOURCE_DIR
    Ressources distribuées avec l'application.
    Lecture seule.
    Compatible développement et PyInstaller.

USER_DIR
    Données propres à l'utilisateur.
    Lecture / écriture.

Règle :

Aucun module ne doit utiliser directement :

    Path("data/...")
    Path("config/...")
    Path("reporting/...")

Tous les chemins doivent être définis ici.
"""

from __future__ import annotations

from pathlib import Path
import sys


# =========================================================
# Détection du mode d'exécution
# =========================================================

if getattr(sys, "frozen", False):
    # -----------------------------------------------------
    # Application compilée PyInstaller
    # -----------------------------------------------------

    # Dossier contenant :
    # Profil Sensoriel.exe
    APP_DIR: Path = Path(
        sys.executable
    ).resolve().parent

    # Dossier temporaire contenant
    # les ressources extraites par PyInstaller
    RESOURCE_DIR: Path = Path(
        getattr(
            sys,
            "_MEIPASS",
            APP_DIR,
        )
    )

else:
    # -----------------------------------------------------
    # Mode développement
    # -----------------------------------------------------

    APP_DIR: Path = Path(
        __file__
    ).resolve().parent.parent

    RESOURCE_DIR: Path = APP_DIR


# =========================================================
# Fonctions utilitaires
# =========================================================

def resource_path(*parts: str) -> Path:
    """
    Retourne un chemin vers une ressource embarquée.

    Exemple :

        resource_path(
            "data",
            "reference",
            "reference.json",
        )
    """

    return RESOURCE_DIR.joinpath(*parts)


def user_path(*parts: str) -> Path:
    """
    Retourne un chemin vers une donnée utilisateur.

    Exemple :

        user_path(
            "Rapports",
            "bilan",
        )
    """

    return USER_DIR.joinpath(*parts)


# =========================================================
# Données utilisateur
# =========================================================

USER_DIR: Path = (
    Path.home()
    / "Documents"
    / "Profil Sensoriel"
)


ENV_FILE: Path = USER_DIR / ".env"


# =========================================================
# Données brutes utilisateur
# =========================================================

RAW_DIR: Path = USER_DIR / "Raw"

LAST_SEEN_FILE: Path = (
    RAW_DIR
    / ".last_seen.json"
)

STATE_PATH: Path = (
    RAW_DIR
    / ".state.json"
)


# =========================================================
# Rapports utilisateur
# =========================================================

REPORT_DIR: Path = (
    USER_DIR
    / "Rapports"
)

JSON_DIR: Path = (
    REPORT_DIR
    / "json"
)

HTML_DIR: Path = (
    REPORT_DIR
    / "html"
)

BILAN_DIR: Path = (
    REPORT_DIR
    / "bilan"
)


def ensure_user_directories() -> None:
    """
    Crée les dossiers utilisateur nécessaires.
    """

    for directory in (
        USER_DIR,
        RAW_DIR,
        REPORT_DIR,
        JSON_DIR,
        HTML_DIR,
        BILAN_DIR,
    ):
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


# Création au chargement du module
ensure_user_directories()


# =========================================================
# Ressources embarquées
# =========================================================

CONFIG_DIR: Path = (
    RESOURCE_DIR
    / "config"
)

DATA_DIR: Path = (
    RESOURCE_DIR
    / "data"
)

REFERENCE_DIR: Path = (
    DATA_DIR
    / "reference"
)

REPORTING_DIR: Path = (
    RESOURCE_DIR
    / "reporting"
)

FAVICON_DIR: Path = (
    RESOURCE_DIR
    / "favicon_io"
)


# =========================================================
# Configuration embarquée
# =========================================================

RUNTIME_JSON: Path = (
    CONFIG_DIR
    / "runtime.json"
)


# =========================================================
# Fichiers de référence métier
# =========================================================

REFERENCE_PATH: Path = (
    REFERENCE_DIR
    / "reference.json"
)

AGES_PATH: Path = (
    REFERENCE_DIR
    / "ages.json"
)

NORMES_PATH: Path = (
    REFERENCE_DIR
    / "normes.json"
)

DOMAINES_SENSORIELS_PATH: Path = (
    REFERENCE_DIR
    / "domaines_sensoriels.json"
)

ENFANT_PATH: Path = (
    REFERENCE_DIR
    / "enfant.json"
)

JEUNE_ENFANT_PATH: Path = (
    REFERENCE_DIR
    / "jeune_enfant.json"
)

SCOLAIRE_PATH: Path = (
    REFERENCE_DIR
    / "scolaire.json"
)

STRATEGIES_PATH: Path = (
    REFERENCE_DIR
    / "strategies.json"
)


# =========================================================
# Templates de génération
# =========================================================

# Templates fixes embarqués
# Utilisés par reporting/

HTML_TEMPLATE: Path = (
    REFERENCE_DIR
    / "template.html"
)

ODT_TEMPLATE: Path = (
    REFERENCE_DIR
    / "template.odt"
)


# =========================================================
# Diagnostic
# =========================================================

def debug_paths() -> None:
    """
    Affiche les chemins principaux.

    Utilisation :

        python test_paths.py
    """

    paths = {
        "APP_DIR": APP_DIR,
        "RESOURCE_DIR": RESOURCE_DIR,
        "USER_DIR": USER_DIR,
        "ENV_FILE": ENV_FILE,
        "REPORT_DIR": REPORT_DIR,
        "RAW_DIR": RAW_DIR,
        "REFERENCE_PATH": REFERENCE_PATH,
        "HTML_TEMPLATE": HTML_TEMPLATE,
        "ODT_TEMPLATE": ODT_TEMPLATE,
        "RUNTIME_JSON": RUNTIME_JSON,
    }

    for name, path in paths.items():
        print(name)
        print(path)
        print()