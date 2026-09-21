from __future__ import annotations

import logging

from .client import ErpApiClient
from .config import Settings
from .storage import MySqlStore
from .sync import Synchronizer


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = Settings.from_environment()
    client = ErpApiClient(settings.base_url, settings.username, settings.password, settings.timeout_seconds, settings.retry_attempts)
    result = Synchronizer(client, MySqlStore(), settings.page_size).sync_all()
    logging.info("Synthetic demonstration completed: %s", result)


if __name__ == "__main__":
    main()
