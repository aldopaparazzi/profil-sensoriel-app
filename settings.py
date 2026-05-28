# D:\Documents\CAO\VSCode\profil-sensoriel-app\config.py
from pathlib import Path

# racine du projet = dossier config.py
ROOT = Path(__file__).resolve().parent

# dossiers standards
DATA_DIR = ROOT / "data"
DEBUG_DIR = DATA_DIR / "debug"
RAW_DIR = DATA_DIR / "raw"
REFERENCE_DIR = DATA_DIR / "reference"

DB_PATH = ROOT / "database" / "sensory.db"