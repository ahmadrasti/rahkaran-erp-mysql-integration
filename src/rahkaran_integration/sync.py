from __future__ import annotations

import logging
from dataclasses import dataclass

from .validation import transform

LOGGER = logging.getLogger(__name__)


@dataclass
class Synchronizer:
    client: object
    store: object
    page_size: int = 3

    def sync_entity(self, entity: str) -> int:
        page, written = 1, 0
        checkpoint = self.store.checkpoint_for(entity)
        while True:
            payload = self.client.fetch_page(entity, page, self.page_size, checkpoint)
            rows = [transform(entity, item) for item in payload["items"]]
            if not rows:
                self.store.add_audit(entity, "success", written, "complete")
                return written
            try:
                with self.store.transaction():
                    self.store.upsert(entity, rows)
                    newest = max(row["updated_at"] for row in rows)
                    self.store.set_checkpoint(entity, newest)
            except Exception as error:
                self.store.add_audit(entity, "failed", written, type(error).__name__)
                LOGGER.exception("Synthetic sync failed for %s", entity)
                raise
            written += len(rows)
            if not payload.get("has_more", False):
                self.store.add_audit(entity, "success", written, "complete")
                return written
            page += 1

    def sync_all(self) -> dict[str, int]:
        return {entity: self.sync_entity(entity) for entity in ("customers", "products", "orders")}
