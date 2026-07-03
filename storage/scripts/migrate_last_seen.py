# storage/scripts/migrate_last_seen.py

#!/usr/bin/env python
"""Crée le fichier .last_seen.json à partir des données existantes."""

import json
from pathlib import Path
from storage.last_seen import update_last_seen

def migrate():
    """Extrait les derniers IDs des fichiers existants."""
    raw_dir = Path("data/raw")
    
    for json_file in raw_dir.glob("*.json"):
        if json_file.name == ".last_seen.json":
            continue
        
        form_name = json_file.stem
        print(f"📖 Traitement de {form_name}...")
        
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            submissions = data.get("submissions", [])
            if submissions:
                last_sub = submissions[-1]
                last_id = last_sub.get("id")
                submitted_at = last_sub.get("submittedAt")
                
                if last_id:
                    update_last_seen(form_name, last_id, submitted_at)
                    print(f"   ✅ ID: {last_id[:8]}...")
                else:
                    print(f"   ⚠️ Pas d'ID trouvé")
            else:
                print(f"   ⚠️ Aucune soumission")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    print("\n✅ Migration terminée")

if __name__ == "__main__":
    migrate()