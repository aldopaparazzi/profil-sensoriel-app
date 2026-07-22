# reporting/odt.py
import shutil
import subprocess
from pathlib import Path

from reporting.paths import BILAN_DIR, ODT_DIR, ODT_TEMPLATE
from reporting.utils import build_report_filename

def generate_bilan(filename: str) -> dict:
    """
    Génère un bilan ODT pour un patient.
    
    Args:
        filename: Nom de base du fichier (sans extension)
    
    Returns:
        dict: Statut de l'opération
    """
    BILAN_DIR.mkdir(parents=True, exist_ok=True)
    
    # On suppose que le template existe
    if not ODT_TEMPLATE.exists():
        return {
            "status": "error",
            "file": None,
            "error": f"Template introuvable: {ODT_TEMPLATE}"
        }
    
    bilan_path = BILAN_DIR / f"{filename}_bilan.odt"
    
    try:
        # Copie du template vers le bilan
        shutil.copy2(ODT_TEMPLATE, bilan_path)
        
        if not bilan_path.exists():
            return {"status": "error", "file": None, "error": "Fichier non créé"}
        
        # Tentative d'ouverture avec LibreOffice
        try:
            open_odt(bilan_path)
            return {"status": "ok", "file": bilan_path, "opened": True}
        except Exception as e:
            return {"status": "warning", "file": bilan_path, "error": str(e)}
            
    except Exception as e:
        return {"status": "error", "file": None, "error": str(e)}

def export_odt(patient: dict, output_dir: str | Path = ODT_DIR) -> Path | None:
    """
    Exporte un ODT à partir des données patient.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = build_report_filename(patient, "odt")
    output_path = output_dir / filename
    
    if not ODT_TEMPLATE.exists():
        print(f"⚠️ Template ODT introuvable: {ODT_TEMPLATE}")
        return None
    
    shutil.copy2(ODT_TEMPLATE, output_path)
    print(f"✓ ODT exported: {output_path}")
    return output_path

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

def open_odt(path: Path):
    """Ouvre un fichier ODT avec LibreOffice."""
    exe = find_libreoffice()
    
    if not exe:
        raise RuntimeError("LibreOffice introuvable")
    
    if not Path(exe).exists():
        raise RuntimeError(f"LibreOffice introuvable: {exe}")
    
    subprocess.Popen([exe, str(path)])