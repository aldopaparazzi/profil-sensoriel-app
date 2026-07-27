# reporting/export.py
import json
from pathlib import Path
from typing import Any

from reporting.html import generate_html_report
from reporting.odt import export_odt
from reporting.utils import build_report_filename
from storage.paths import paths


def export_json(
    report: dict[str, Any],
    patient: dict[str, Any],
    output_dir: str | Path = paths.json_dir,
) -> Path:
    """
    Exporte le rapport en JSON.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = build_report_filename(patient, "json")
    output_path = output_dir / filename

    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"✓ JSON exported: {output_path}")
    return output_path


def export_html(
    report: dict[str, Any],
    patient: dict[str, Any],
    output_dir: str | Path = paths.html_dir,
) -> Path | None:
    """
    Exporte le rapport en HTML.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = build_report_filename(patient, "html")
    output_path = output_dir / filename

    try:
        return generate_html_report(report, output_path)
    except Exception as e:  # noqa: BLE001
        print(f"✗ Erreur génération HTML: {e}")
        return None


def export_odt_report(
    patient: dict[str, Any], output_dir: str | Path = paths.bilan_dir
) -> Path | None:
    """
    Exporte le rapport en ODT.
    """
    try:
        return export_odt(patient, output_dir)
    except Exception as e:  # noqa: BLE001
        print(f"✗ Erreur génération ODT: {e}")
        return None


def export_all(
    report: dict[str, Any],
    patient: dict[str, Any],
    generate_html: bool = True,
    generate_odt: bool = True,
) -> dict:
    """
    Exporte le rapport dans tous les formats demandés.

    Returns:
        dict: Chemins des fichiers exportés
    """
    result = {
        "json": export_json(report, patient),
        "html": None,
        "odt": None,
    }

    if generate_html:
        result["html"] = export_html(report, patient)

    if generate_odt:
        result["odt"] = export_odt_report(patient)

    return result
