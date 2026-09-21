"""Wait for the local synthetic mock service without printing environment data."""
from __future__ import annotations

import time
from urllib.request import urlopen


for _ in range(20):
    try:
        with urlopen("http://127.0.0.1:8000/api/v1/orders", timeout=2):
            raise SystemExit(0)
    except OSError:
        time.sleep(1)
raise SystemExit("synthetic mock service did not become ready")
