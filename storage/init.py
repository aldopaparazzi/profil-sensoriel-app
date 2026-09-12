# storage/init.py
import json
import logging

from storage.paths import paths  # ENV_FILE, RUNTIME_JSON

logger = logging.getLogger(__name__)


def ensure_env():
    """
    S'assure que le dossier local de configuration
    et le fichier .env existent.
    """
    paths.env_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    if not paths.env_file.exists():
        paths.env_file.write_text(
            "",
            encoding="utf-8",
        )

def load_runtime() -> dict:
    try:
        return json.loads(paths.runtime_json.read_text(encoding="utf-8"))
    except FileNotFoundError:
        try:
            defaults = json.loads(paths.default_runtime_json.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            defaults = {}
        defaults.pop("workspace", None)  # jamais hérité : toujours demandé à l'utilisateur
        save_runtime(defaults)
        return defaults
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Impossible de charger runtime.json : %s", e)
        return {}


def save_runtime(config: dict) -> None:
    paths.runtime_json.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    paths.runtime_json.write_text(
        json.dumps(
            config,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
