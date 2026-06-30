#!/usr/bin/env python
"""
Script pour régénérer tous les rapports HTML à partir des JSON existants.
Utile après une modification du template HTML.
"""

import json
from pathlib import Path
from reporting.generate_html import batch_generate_html

def main():
    # Dossiers source et destination
    report_dir = Path("data/report")
    html_dir = Path("data/report/html")
    reference_path = Path("data/reference/reference.json")
    
    # Créer le dossier de sortie
    html_dir.mkdir(parents=True, exist_ok=True)
    
    print("🔄 Régénération des rapports HTML...")
    batch_generate_html(report_dir, reference_path, html_dir)
    print("✅ Terminé")

if __name__ == "__main__":
    main()