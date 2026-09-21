from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
import os


class StorageError(RuntimeError):
    pass


@dataclass
class MemoryStore:
    records: dict[str, dict[str, dict]] = field(default_factory=lambda: {"customers": {}, "products": {}, "orders": {}})
    checkpoints: dict[str, str] = field(default_factory=dict)
    audit: list[dict] = field(default_factory=list)
    fail_next: bool = False

    @contextmanager
    def transaction(self):
        if self.fail_next:
            self.fail_next = False
            raise StorageError("synthetic storage failure")
        yield self

    def upsert(self, entity: str, rows: list[dict]) -> None:
        key = f"{entity[:-1]}_id"
        for row in rows:
            self.records[entity][str(row[key])] = dict(row)

    def checkpoint_for(self, entity: str) -> str | None:
        return self.checkpoints.get(entity)

    def set_checkpoint(self, entity: str, value: str) -> None:
        self.checkpoints[entity] = value

    def add_audit(self, entity: str, outcome: str, rows: int, detail: str) -> None:
        self.audit.append({"entity": entity, "outcome": outcome, "rows": rows, "detail": detail})


class MySqlStore:
    """Small generic MySQL adapter; callers provide no production-specific schema."""

    def __init__(self, connection_factory=None):
        self.connection_factory = connection_factory or self._connect
        self.connection = self.connection_factory()

    def _connect(self):
        try:
            import pymysql
        except ImportError as error:
            raise StorageError("Install pymysql to use the optional MySQL demo adapter") from error
        return pymysql.connect(
            host=os.environ.get("MYSQL_HOST", "mysql"), port=int(os.environ.get("MYSQL_PORT", "3306")),
            user=os.environ.get("MYSQL_USER", "demo_user"), password=os.environ.get("MYSQL_PASSWORD", "demo_password"),
            database=os.environ.get("MYSQL_DATABASE", "erp_demo"), autocommit=False,
        )

    @contextmanager
    def transaction(self):
        try:
            yield self
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def _table(self, entity: str) -> str:
        if entity not in {"customers", "products", "orders"}:
            raise StorageError("unsupported generic entity")
        return f"erp_{entity}"

    def upsert(self, entity: str, rows: list[dict]) -> None:
        if not rows:
            return
        table = self._table(entity)
        columns = list(rows[0])
        placeholders = ", ".join(["%s"] * len(columns))
        updates = ", ".join(f"{column}=VALUES({column})" for column in columns if not column.endswith("_id"))
        statement = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates}"
        with self.connection.cursor() as cursor:
            cursor.executemany(statement, [tuple(row[column] for column in columns) for row in rows])

    def checkpoint_for(self, entity: str) -> str | None:
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT checkpoint_value FROM sync_state WHERE entity_name=%s", (entity,))
            row = cursor.fetchone()
        return row[0] if row else None

    def set_checkpoint(self, entity: str, value: str) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO sync_state (entity_name, checkpoint_value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE checkpoint_value=VALUES(checkpoint_value)", (entity, value))

    def add_audit(self, entity: str, outcome: str, rows: int, detail: str) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO api_audit_log (entity_name, outcome, row_count, detail) VALUES (%s, %s, %s, %s)", (entity, outcome, rows, detail))
