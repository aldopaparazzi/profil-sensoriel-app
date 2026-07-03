# reporting/generate_html.py
# Génère un rapport HTML autonome (data + référence injectées en dur)
# à partir d'un data.json (sortie du pipeline) et de reference.json.

import json
from pathlib import Path
from typing import Dict, Any #, Optional

TEMPLATE_PATH = Path(__file__).resolve().parent / "template_resultat.html"

def generate_html_report(data: Dict[str, Any], reference: Dict[str, Any], output_path: str | Path) -> Path:
    """
    Injecte `data` (objet patient/domains/quadrants/...) et `reference`
    (questions par form_type) dans le template HTML, puis écrit
    le résultat dans output_path.

    - data       : dict, structure identique à data.json (1 submission)
    - reference  : dict, structure identique à reference.json (tous form_types)
    - output_path: chemin du fichier .html à générer
    """
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    data_json = json.dumps(data, ensure_ascii=False)
    reference_json = json.dumps(reference, ensure_ascii=False)

    # Remplacement des placeholders.
    # NB: on utilise .replace() (pas de Jinja) pour rester dépendance-free
    # et garder le HTML ouvrable tel quel par un humain qui voudrait l'éditer.
    html = template.replace("__DATA_JSON__", data_json)
    html = html.replace("__REFERENCE_JSON__", reference_json)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    return output_path

def generate_from_report(report_path: str | Path, reference_path: str | Path, output_path: str | Path) -> Path:
    """
    Génère un HTML à partir d'un fichier report.json déjà existant.
    Utile pour régénérer des rapports sans relancer tout le pipeline.
    """
    with open(report_path, encoding="utf-8") as f:
        data = json.load(f)

    with open(reference_path, encoding="utf-8") as f:
        reference = json.load(f)

    return generate_html_report(data, reference, output_path)

def generate_from_files(data_path: str | Path, reference_path: str | Path, output_path: str | Path) -> Path:
    """Variante pratique : lit data.json et reference.json depuis le disque."""

    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)

    with open(reference_path, encoding="utf-8") as f:
        reference = json.load(f)

    return generate_html_report(data, reference, output_path)

def batch_generate_html(input_dir: str | Path, reference_path: str | Path, output_dir: str | Path):
    """
    Génère des rapports HTML pour tous les fichiers JSON dans un dossier.
    Utile pour la génération en lot.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(reference_path, encoding="utf-8") as f:
        reference = json.load(f)

    for json_file in input_dir.glob("*.json"):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
            
            # Construire le nom de sortie
            output_file = output_dir / json_file.with_suffix(".html").name
            generate_html_report(data, reference, output_file)
            print(f"✅ {output_file}")
        except Exception as e:
            print(f"❌ Erreur sur {json_file.name}: {e}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python generate_html.py <data.json> <reference.json> <sortie.html>")
        print("  python generate_html.py --batch <dossier_json> <reference.json> <dossier_sortie>")
        sys.exit(1)
    # Usage en ligne de commande :
    #   python generate_html.py data.json reference.json sortie.html
    if sys.argv[1] == "--batch":
        if len(sys.argv) != 5:
            print("Usage: python generate_html.py --batch <dossier_json> <reference.json> <dossier_sortie>")
            sys.exit(1)
        _, _, input_dir, reference_path, output_dir = sys.argv
        batch_generate_html(input_dir, reference_path, output_dir)
    else:
        if len(sys.argv) != 4:
            print("Usage: python generate_html.py <data.json> <reference.json> <sortie.html>")
            sys.exit(1)
        data_path, reference_path, output_path = sys.argv[1:4]
        result = generate_from_files(data_path, reference_path, output_path)
    print(f"✅ Rapport généré : {result}")