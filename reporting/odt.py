# reporting/odt.py

import shutil
import subprocess
from pathlib import Path

from reporting.utils import build_report_filename
from storage.paths import paths
from utils.logger import get_logger
from utils.privacy import anonymize_patient

logger = get_logger(__name__)

def find_libreoffice() -> str | None:
    """Trouve l'exécutable LibreOffice."""
    # Chemins possibles sur Windows
    windows_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]

    for path in windows_paths:
        if Path(path).exists():
            return path

    # Recherche dans le PATH
    return shutil.which("soffice") or shutil.which("libreoffice")

def is_locked(path: Path) -> bool:
    """Détecte si un fichier ODT est actuellement ouvert dans LibreOffice."""
    lock_file = path.parent / f".~lock.{path.name}#"
    return lock_file.exists()

def generate_bilan(filename: str) -> dict:
    """
    Génère un bilan ODT pour un patient.

    Args:
        filename: Nom de base du fichier (sans extension)

    Returns:
        dict: Statut de l'opération
    """
    paths.bilan_dir.mkdir(parents=True, exist_ok=True)

    # On suppose que le template existe
    if not paths.odt_template.exists():
        return {
            "status": "error",
            "file": None,
            "error": f"Template introuvable: {paths.odt_template}",
        }

    bilan_path = paths.bilan_dir / f"{filename}_bilan.odt"

    try:
        # Copie du template vers le bilan
        shutil.copy2(paths.odt_template, bilan_path)

        if not bilan_path.exists():
            return {"status": "error", "file": None, "error": "Fichier non créé"}

        # Tentative d'ouverture avec LibreOffice
        try:
            open_odt(bilan_path)
            return {"status": "ok", "file": bilan_path, "opened": True}
        except Exception as e:  # noqa: BLE001
            return {"status": "warning", "file": bilan_path, "error": str(e)}

    except Exception as e:  # noqa: BLE001
        return {"status": "error", "file": None, "error": str(e)}

def export_odt(patient: dict, output_dir: str | Path = paths.bilan_dir) -> Path | None:
    """
    Exporte un ODT à partir des données patient.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = build_report_filename(patient, "odt")
    output_path = output_dir / filename

    if not paths.odt_template.exists():
        logger.warning("⚠️ Template ODT introuvable : %s", paths.odt_template)
        return None

    shutil.copy2(paths.odt_template, output_path)
    logger.debug(
        "Chemin complet ODT (%s) : %s", anonymize_patient(patient), output_path
    )
    return output_path

def open_odt(path: Path) -> bool:
    """
    Ouvre un fichier ODT avec LibreOffice.
    """
    exe = paths.libreoffice
    if not exe:
        return False
    try:
        subprocess.Popen(
            [
                str(exe),
                str(path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:  # noqa: BLE001
        return False
