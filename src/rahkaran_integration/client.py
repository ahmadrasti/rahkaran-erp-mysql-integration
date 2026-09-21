from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ApiTransportError(RuntimeError):
    """A transient or malformed response from the configured API."""


@dataclass
class ErpApiClient:
    base_url: str
    username: str
    password: str
    timeout_seconds: float = 2.0
    retry_attempts: int = 3
    opener: Callable = urlopen
    sleeper: Callable[[float], None] = time.sleep

    def _authorization(self) -> str:
        credentials = f"{self.username}:{self.password}".encode("utf-8")
        return "Basic " + base64.b64encode(credentials).decode("ascii")

    def fetch_page(self, entity: str, page: int, page_size: int, since: str | None = None) -> dict:
        if entity not in {"orders", "customers", "products"}:
            raise ValueError("unsupported synthetic entity")
        query = {"page": page, "page_size": page_size}
        if since:
            query["since"] = since
        url = f"{self.base_url.rstrip('/')}/api/v1/{entity}?{urlencode(query)}"
        request = Request(url, headers={"Authorization": self._authorization(), "Accept": "application/json"})
        last_error: Exception | None = None
        for attempt in range(self.retry_attempts):
            try:
                with self.opener(request, timeout=self.timeout_seconds) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
                    raise ApiTransportError("response must be an object with an items list")
                return payload
            except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, ApiTransportError) as error:
                last_error = error
                if attempt + 1 < self.retry_attempts:
                    self.sleeper(0.1 * (2**attempt))
        raise ApiTransportError("request failed after configured retries") from last_error
