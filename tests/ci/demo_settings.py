"""Load checked-in synthetic CI values without echoing them in workflow logs."""
from __future__ import annotations

import os
from pathlib import Path


def load_ci_settings() -> None:
    for line in (Path(__file__).parents[2] / ".env.example").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ[key] = value
    os.environ["ERP_BASE_URL"] = "http://127.0.0.1:8000"
    os.environ["MYSQL_HOST"] = "127.0.0.1"
    os.environ["MYSQL_USER"] = "root"
    os.environ["MYSQL_PASSWORD"] = ""
