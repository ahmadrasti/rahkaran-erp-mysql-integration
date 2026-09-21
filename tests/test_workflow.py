import json
import sys
import unittest
from pathlib import Path
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from rahkaran_integration.client import ApiTransportError, ErpApiClient
from rahkaran_integration.storage import MemoryStore, StorageError
from rahkaran_integration.sync import Synchronizer
from rahkaran_integration.validation import ValidationError, transform, validate
from mock_server.app import synthetic_rows


class FakeClient:
    def __init__(self, pages): self.pages, self.calls = pages, []
    def fetch_page(self, entity, page, page_size, since):
        self.calls.append((entity, page, page_size, since))
        return self.pages[page - 1] if page <= len(self.pages) else {"items": [], "has_more": False}


def order(number, stamp):
    return {"order_id": f"O-{number}", "customer_id": "C-001", "product_id": "P-001", "order_date": "2026-01-01", "quantity": 1, "unit_price": 10.0, "status": "created", "updated_at": stamp}


class WorkflowTests(unittest.TestCase):
    def test_pagination_checkpoint_and_idempotent_upsert(self):
        client = FakeClient([{"items": [order(1, "2026-01-01T00:01:00+00:00")], "has_more": True}, {"items": [order(2, "2026-01-01T00:02:00+00:00")], "has_more": False}])
        store = MemoryStore()
        self.assertEqual(Synchronizer(client, store, page_size=1).sync_entity("orders"), 2)
        self.assertEqual(len(store.records["orders"]), 2)
        self.assertEqual(store.checkpoint_for("orders"), "2026-01-01T00:02:00+00:00")
        repeat = FakeClient([{"items": [order(2, "2026-01-01T00:02:00+00:00")], "has_more": False}])
        Synchronizer(repeat, store).sync_entity("orders")
        self.assertEqual(len(store.records["orders"]), 2)
        self.assertEqual(repeat.calls[0][3], "2026-01-01T00:02:00+00:00")

    def test_interrupted_write_does_not_advance_checkpoint(self):
        store = MemoryStore(fail_next=True)
        client = FakeClient([{"items": [order(1, "2026-01-01T00:01:00+00:00")], "has_more": False}])
        with self.assertRaises(StorageError): Synchronizer(client, store).sync_entity("orders")
        self.assertIsNone(store.checkpoint_for("orders"))
        self.assertEqual(store.audit[-1]["outcome"], "failed")

    def test_validation_and_transformation(self):
        with self.assertRaises(ValidationError): validate("orders", {"order_id": "missing"})
        row = order(1, "2026-01-01T00:01:00+00:00"); row["status"] = " created "
        self.assertEqual(transform("orders", row)["status"], "created")

    def test_retry_then_success(self):
        calls, sleeps = [], []
        class Response:
            def read(self): return json.dumps({"items": [], "has_more": False}).encode()
            def __enter__(self): return self
            def __exit__(self, *_): return False
        def opener(*_args, **_kwargs):
            calls.append(1)
            if len(calls) == 1: raise URLError("synthetic transient failure")
            return Response()
        client = ErpApiClient("http://mock-erp:8000", "demo_user", "demo_password", opener=opener, sleeper=sleeps.append)
        self.assertEqual(client.fetch_page("orders", 1, 3)["items"], [])
        self.assertEqual(sleeps, [0.1])

    def test_retry_exhaustion_and_unknown_entity(self):
        def failing(*_args, **_kwargs): raise URLError("synthetic failure")
        client = ErpApiClient("http://mock-erp:8000", "demo_user", "demo_password", retry_attempts=1, opener=failing, sleeper=lambda _: None)
        with self.assertRaises(ApiTransportError): client.fetch_page("orders", 1, 3)
        with self.assertRaises(ValueError): client.fetch_page("unknown", 1, 3)

    def test_mock_service_data_is_deterministic_and_synthetic(self):
        self.assertEqual(synthetic_rows("orders"), synthetic_rows("orders"))
        self.assertEqual(len(synthetic_rows("customers")), 7)
