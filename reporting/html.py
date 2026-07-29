# reporting/html.py
import json
from functools import cache
from pathlib import Path
from typing import Any  # , Dict

from storage.paths import paths  # HTML_TEMPLATE, REFERENCE_PATH


@cache
def load_reference():
    """Charge la référence avec cache."""
    with paths.reference_path.open(encoding="utf-8") as f:
        return json.load(f)


def generate_html_report(data: dict[str, Any], output_path: str | Path) -> Path:
    """
    Génère un rapport HTML à partir des données.

    Args:
        data: Données du rapport
        output_path: Chemin de sortie du fichier HTML

    Returns:
        Path: Chemin du fichier généré
    """
    reference = load_reference()
    template = paths.html_template.read_text(encoding="utf-8")

    data_json = json.dumps(data, ensure_ascii=False)
    reference_json = json.dumps(reference, ensure_ascii=False)

    html = template.replace("__DATA_JSON__", data_json).replace(
        "__REFERENCE_JSON__", reference_json
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    return output_path


def batch_generate_html(input_dir: str | Path, output_dir: str | Path):
    """
    Génère des rapports HTML pour tous les fichiers JSON dans un dossier.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    reference = load_reference()
    print(f"Référence chargée avec {len(reference)} entrées.")

    for json_file in input_dir.glob("*.json"):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"❌ Erreur lecture JSON {json_file.name}: {e}")
            raise ValueError(f"Impossible de lire {json_file.name}") from e

        try:
            output_file = output_dir / json_file.with_suffix(".html").name
            generate_html_report(data, output_file)
            print(f"✅ {output_file}")
        except Exception as e:
            print(f"❌ Erreur génération HTML {json_file.name}: {e}")
            raise
