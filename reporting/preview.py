import os
import subprocess
import uuid
from pathlib import Path

from storage.paths import paths
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_preview_png(
    scores: dict,
    tmp_dir: Path,
    chart_config: dict | None = None,
    column_config: dict | None = None,
) -> Path | None:
    """Génère un ODT d'aperçu puis le convertit en PNG via LibreOffice."""
    from reporting.bilan_odt import build_preview_odt

    tmp_dir.mkdir(parents=True, exist_ok=True)
    odt_path = tmp_dir / "settings_preview.odt"
    png_path = tmp_dir / "settings_preview.png"

    if png_path.exists():
        png_path.unlink()

    build_preview_odt(
        scores,
        odt_path,
        chart_config=chart_config,
        column_config=column_config,
    )

    exe = paths.libreoffice
    if not exe:
        logger.warning("LibreOffice introuvable, aperçu impossible")
        return None

    profile_dir = tmp_dir / f"lo_profile_{uuid.uuid4().hex}"

    result = subprocess.run(
        [
            str(exe),
            "--headless",
            f"-env:UserInstallation=file:///{profile_dir.as_posix()}",
            "--convert-to",
            "png",
            "--outdir",
            str(tmp_dir),
            str(odt_path),
        ],
        capture_output=True,
        timeout=15,
        check=False,
    )

    logger.debug("LibreOffice returncode: %s", result.returncode)
    if result.stderr:
        stderr = result.stderr.decode(errors="replace").strip()

        if result.returncode != 0:
            logger.error("LibreOffice stderr: %s", stderr)
        else:
            logger.debug("LibreOffice stderr: %s", stderr)

    return png_path if png_path.exists() else None
