"""Run the real integration application with local synthetic CI configuration."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from demo_settings import load_ci_settings

load_ci_settings()

from rahkaran_integration.main import main

main()
