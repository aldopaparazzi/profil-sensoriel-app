# storage/init.py

from storage.paths import ENV_FILE

def ensure_env():
    if not ENV_FILE.exists():
        ENV_FILE.write_text(
            "",
            encoding="utf-8"
        )
