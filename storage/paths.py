"""
storage.paths
=============

Gestion centralisée des chemins de l'application Profil Sensoriel.

Principe
--------

Toutes les parties de l'application utilisent uniquement
l'objet global :

    paths

Exemple :

    from storage.paths import paths

    paths.html_dir
    paths.json_dir
    paths.bilan_dir
    paths.env_file

Le workspace est relu automatiquement depuis
config/runtime.json à chaque accès.

Ainsi, si l'utilisateur change le dossier de travail
dans l'interface, aucun redémarrage n'est nécessaire.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# ============================================================
# Classe Paths
# ============================================================


class Paths:
    """
    Fournit tous les chemins utilisés par l'application.

    Les chemins dépendant du workspace sont recalculés
    dynamiquement à chaque accès.
    """

    # --------------------------------------------------------
    # runtime.json
    # --------------------------------------------------------

    @property
    def runtime(self) -> dict:
        """
        Charge runtime.json.

        Retourne un dictionnaire vide si le fichier
        est absent ou invalide.
        """

        try:
            return json.loads(self.runtime_json.read_text(encoding="utf-8"))

        except (
            FileNotFoundError,
            json.JSONDecodeError,
            OSError,
        ):
            return {}

    # --------------------------------------------------------
    # Dossiers de l'application
    # --------------------------------------------------------

    @property
    def app_dir(self) -> Path:
        """
        Dossier de  l'application.
        """
        if getattr(sys, "frozen", False):
            dir = Path(sys.executable).resolve().parent
        else:
            dir = Path(__file__).resolve().parent.parent
        return dir
    
    @property
    def resource_dir(self) -> Path:
        """
        Dossier des ressources embarquées.
        """
        if getattr(sys, "frozen", False):
            dir = Path(getattr(sys, "_MEIPASS", self.app_dir))
        else:
            dir = self.app_dir

        return dir

    @property
    def config_dir(self) -> Path:
        """
        Dossier de configuration.
        """
        return self.resource_dir / "config"

    @property
    def runtime_json(self) -> Path:
        """
        Fichier runtime.json.
        """
        return self.config_dir / "runtime.json"    

    # --------------------------------------------------------
    # Workspace
    # --------------------------------------------------------

    @property
    def workspace(self) -> Path:
        """
        Dossier de travail utilisateur.
        """

        ws = self.runtime.get("workspace")

        if ws:
            return Path(ws).expanduser()

        return Path.home() / "Documents" / "Profil Sensoriel"

    # --------------------------------------------------------
    # Dossiers utilisateur
    # --------------------------------------------------------

    @property
    def env_file(self) -> Path:
        return self.workspace / ".env"

    @property
    def raw_dir(self) -> Path:
        return self.workspace / "Raw"

    @property
    def last_seen_file(self) -> Path:
        return self.raw_dir / ".last_seen.json"

    @property
    def state_file(self) -> Path:
        return self.raw_dir / ".state.json"

    @property
    def report_dir(self) -> Path:
        return self.workspace / "Rapports"

    @property
    def html_dir(self) -> Path:
        return self.report_dir / "html"

    @property
    def json_dir(self) -> Path:
        return self.report_dir / "json"

    @property
    def bilan_dir(self) -> Path:
        return self.report_dir / "bilan"

    # --------------------------------------------------------
    # Ressources embarquées
    # --------------------------------------------------------

    @property
    def data_dir(self) -> Path:
        return self.resource_dir / "data"

    @property
    def reference_dir(self) -> Path:
        return self.data_dir / "reference"

    @property
    def favicon_dir(self) -> Path:
        return self.resource_dir / "favicon_io"

    @property
    def reporting_dir(self) -> Path:
        return self.resource_dir / "reporting"

    # --------------------------------------------------------
    # Templates
    # --------------------------------------------------------

    @property
    def html_template(self) -> Path:
        return self.reference_dir / "template.html"

    @property
    def odt_template(self) -> Path:
        return self.reference_dir / "template.odt"

    # --------------------------------------------------------
    # Références métier
    # --------------------------------------------------------

    @property
    def reference_path(self) -> Path:
        return self.reference_dir / "reference.json"

    @property
    def normes_path(self) -> Path:
        return self.reference_dir / "normes.json"

    @property
    def ages_path(self) -> Path:
        return self.reference_dir / "ages.json"

    @property
    def strategies_path(self) -> Path:
        return self.reference_dir / "strategies.json"

    @property
    def enfant_path(self) -> Path:
        return self.reference_dir / "enfant.json"

    @property
    def jeune_enfant_path(self) -> Path:
        return self.reference_dir / "jeune_enfant.json"

    @property
    def scolaire_path(self) -> Path:
        return self.reference_dir / "scolaire.json"

    @property
    def domaines_sensoriels_path(self) -> Path:
        return self.reference_dir / "domaines_sensoriels.json"

    # --------------------------------------------------------
    # Ressources externes
    # --------------------------------------------------------

    @property
    def libreoffice(self) -> Path | None:
        """
        Retourne LibreOffice.

        Priorité :
        1. chemin configuré par l'utilisateur ;
        2. détection automatique.
        """

        configured = self.runtime.get("libreoffice")

        if configured:
            exe = Path(configured)
            if exe.exists():
                return exe

        candidates = (
            Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
            Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
        )

        for exe in candidates:
            if exe.exists():
                return exe

        for name in ("soffice", "libreoffice"):
            exe = shutil.which(name)
            if exe:
                return Path(exe)

        return None

    # --------------------------------------------------------
    # Création des dossiers
    # --------------------------------------------------------

    def ensure_workspace(self):
        """
        Crée les dossiers utilisateur.
        """

        for directory in (
            self.workspace,
            self.raw_dir,
            self.report_dir,
            self.html_dir,
            self.json_dir,
            self.bilan_dir,
        ):
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

    # --------------------------------------------------------
    # Diagnostic
    # --------------------------------------------------------

    def debug(self):

        print("APP_DIR              :", self.app_dir)
        print("RESOURCE_DIR         :", self.resource_dir)
        print("WORKSPACE            :", self.workspace)
        print("REPORT_DIR           :", self.report_dir)
        print("HTML_DIR             :", self.html_dir)
        print("JSON_DIR             :", self.json_dir)
        print("BILAN_DIR            :", self.bilan_dir)
        print("ENV_FILE             :", self.env_file)
        print("RUNTIME_JSON         :", self.runtime_json)


# ============================================================
# Instance globale
# ============================================================

paths = Paths()

paths.ensure_workspace()


if __name__ == "__main__":
    paths.debug()
