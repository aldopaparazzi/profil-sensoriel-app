from pathlib import Path
from datetime import datetime
import shutil

def save_raw_csv(df, form_type: str, base_dir: Path):
    raw_dir = base_dir / "data/raw"
    archive_dir = raw_dir / "archive"

    raw_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    latest_path = raw_dir / f"{form_type}_latest.csv"
    archive_path = archive_dir / f"{form_type}_{timestamp}.csv"

    # 1. overwrite latest
    df.to_csv(latest_path, index=False, encoding="utf-8")

    # 2. archive snapshot
    df.to_csv(archive_path, index=False, encoding="utf-8")

    return latest_path