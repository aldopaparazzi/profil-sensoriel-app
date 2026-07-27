# storage/init.py
import json
import logging

from storage.paths import paths  # ENV_FILE, RUNTIME_JSON

logger = logging.getLogger(__name__)


def ensure_env():
    if not paths.env_file.exists():
        paths.env_file.write_text("", encoding="utf-8")


def load_runtime() -> dict:
    try:
        return json.loads(paths.runtime_json.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Impossible de charger runtime.json : %s", e)
        return {}


def save_runtime(config: dict) -> None:
    paths.runtime_json.write_text(
        json.dumps(
            config,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
