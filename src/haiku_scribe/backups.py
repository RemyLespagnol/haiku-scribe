from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from shutil import copy2


def backup_existing(path: Path, backup_root: Path) -> Path | None:
    if not path.exists():
        return None
    backup_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_root / f"{timestamp}-{path.name}.bak"
    copy2(path, backup_path)
    return backup_path

