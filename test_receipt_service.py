import pytest

from receipt_service import InfraiClient, WorkOrder, issue_receipt


class FakeClient(InfraiClient):
    def __init__(self):
        super().__init__("test-key")
        self.seen = None

    def generate_pdf(self, order):
        self.seen = order.order_id
        return {"ok": True, "data": {"job_id": "job-1"}}


def test_completed_paid_order_issues_receipt():
    client = FakeClient()
    order = WorkOrder("WO-1", "Shop", 5000, "USD", "Tech", "completed", (), "Call tomorrow")
    assert issue_receipt(order, client)["data"]["job_id"] == "job-1"
    assert client.seen == "WO-1"


def test_open_dispatch_is_not_receiptable():
    order = WorkOrder("WO-2", "Shop", 5000, "USD", "Tech", "en_route", (), "Call tomorrow")
    with pytest.raises(ValueError, match="completed dispatch"):
        issue_receipt(order, FakeClient())
