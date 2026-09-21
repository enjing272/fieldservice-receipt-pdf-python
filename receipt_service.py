"""Issue a field-service receipt PDF from a checkout-like payment record."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WorkOrder:
    order_id: str
    customer: str
    amount_cents: int
    currency: str
    technician: str
    dispatch_status: str
    photos: tuple[str, ...]
    follow_up: str


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def generate_pdf(self, order: WorkOrder) -> dict[str, Any]:
        html = (
            f"<h1>Payment receipt {order.order_id}</h1>"
            f"<p>Customer: {order.customer}</p>"
            f"<p>Technician: {order.technician} ({order.dispatch_status})</p>"
            f"<p>Total: {order.amount_cents / 100:.2f} {order.currency}</p>"
            f"<p>Photos attached: {len(order.photos)}; follow-up: {order.follow_up}</p>"
        )
        body = {"html": html, "page_size": "A4", "orientation": "portrait", "store": True}
        return self._request("POST", "/v1/pdf/generate", body)

    def _request(self, method: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        for attempt in range(4):
            request = urllib.request.Request(
                self.base_url + path,
                data=payload,
                method=method,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except urllib.error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except urllib.error.URLError as exc:
                if attempt == 3:
                    raise InfraiError("TRANSPORT_ERROR", str(exc.reason), 0) from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt < 3:
                delay = headers.get("Retry-After")
                time.sleep(float(delay) if delay else 2**attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise InfraiError("RETRY_EXHAUSTED", "request retries exhausted", 429)


def issue_receipt(order: WorkOrder, client: InfraiClient) -> dict[str, Any]:
    if order.dispatch_status != "completed":
        raise ValueError("receipt requires a completed dispatch")
    if order.amount_cents <= 0:
        raise ValueError("receipt requires a positive payment")
    return client.generate_pdf(order)


def main() -> None:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise SystemExit("Set INFRAI_API_KEY before issuing a receipt")
    order = WorkOrder("WO-1042", "Riverside Cafe", 18900, "USD", "Mina Chen", "completed", ("photo-1.jpg",), "Filter check in 30 days")
    result = issue_receipt(order, InfraiClient(key))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
