# utils/json_utils.py

import json
from pathlib import Path
from typing import Any, Dict

def safe_load_json(path: str | Path, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    Charge un fichier JSON avec gestion d'erreur d'encodage.
    
    Tente plusieurs encodages si nécessaire.
    """
    path = Path(path)
    
    encodings = [encoding, "utf-8-sig", "cp1252", "latin-1"]
    
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                return json.load(f)
        except UnicodeDecodeError:
            continue
        except Exception:
            continue
    
    # Fallback ultime: lecture binaire
    try:
        with open(path, "rb") as f:
            content = f.read()
            # Tentative de décodage avec remplacement
            text = content.decode("utf-8", errors="replace")
            return json.loads(text)
    except Exception as e:
        raise ValueError(f"Impossible de lire {path}: {e}")
    
    raise ValueError(f"Impossible de décoder {path}")