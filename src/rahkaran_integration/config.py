from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    base_url: str
    username: str
    password: str
    page_size: int = 3
    timeout_seconds: float = 2.0
    retry_attempts: int = 3

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            base_url=os.environ.get("ERP_BASE_URL", "http://mock-erp:8000"),
            username=os.environ.get("ERP_USERNAME", "demo_user"),
            password=os.environ.get("ERP_PASSWORD", "demo_password"),
            page_size=int(os.environ.get("SYNC_PAGE_SIZE", "3")),
            timeout_seconds=float(os.environ.get("REQUEST_TIMEOUT_SECONDS", "2")),
            retry_attempts=int(os.environ.get("RETRY_ATTEMPTS", "3")),
        )
