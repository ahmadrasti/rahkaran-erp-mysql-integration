import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from rahkaran_integration.storage import MySqlStore


class Cursor:
    def __init__(self, statements): self.statements = statements
    def execute(self, statement, values): self.statements.append((statement, values))
    def __enter__(self): return self
    def __exit__(self, *_): return False


class Connection:
    def __init__(self): self.statements, self.commits = [], 0
    def cursor(self): return Cursor(self.statements)
    def commit(self): self.commits += 1
    def rollback(self): pass


class MySqlStoreTests(unittest.TestCase):
    def test_audit_record_is_committed(self):
        connection = Connection()
        MySqlStore(lambda: connection).add_audit("orders", "success", 7, "complete")
        self.assertEqual(connection.commits, 1)
        self.assertEqual(len(connection.statements), 1)
