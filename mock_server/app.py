from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


def synthetic_rows(entity: str) -> list[dict]:
    stamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
    if entity == "customers":
        return [{"customer_id": f"C-{i:03d}", "name": f"Sample Customer {i}", "updated_at": (stamp + timedelta(minutes=i)).isoformat()} for i in range(1, 8)]
    if entity == "products":
        return [{"product_id": f"P-{i:03d}", "name": f"Sample Product {i}", "unit_price": float(i * 10), "updated_at": (stamp + timedelta(minutes=i)).isoformat()} for i in range(1, 8)]
    if entity == "orders":
        return [{"order_id": f"O-{i:03d}", "customer_id": f"C-{((i - 1) % 7) + 1:03d}", "product_id": f"P-{((i - 1) % 7) + 1:03d}", "order_date": "2026-01-01", "quantity": i, "unit_price": float(i * 10), "status": "created", "updated_at": (stamp + timedelta(minutes=i)).isoformat()} for i in range(1, 8)]
    return []


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        parts = parsed.path.strip("/").split("/")
        if len(parts) != 3 or parts[:2] != ["api", "v1"] or parts[2] not in {"orders", "customers", "products"}:
            self.send_error(404)
            return
        query = parse_qs(parsed.query)
        page = max(1, int(query.get("page", ["1"])[0]))
        page_size = max(1, min(100, int(query.get("page_size", ["3"])[0])))
        rows = synthetic_rows(parts[2])
        since = query.get("since", [None])[0]
        if since:
            rows = [row for row in rows if row["updated_at"] > since]
        start = (page - 1) * page_size
        payload = {"items": rows[start : start + page_size], "has_more": start + page_size < len(rows)}
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *_args: object) -> None:
        return


def main() -> None:
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()


if __name__ == "__main__":
    main()
