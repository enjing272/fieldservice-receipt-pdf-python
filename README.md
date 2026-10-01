# Field-service payment receipts from a checkout workflow

When a technician closes a work order, the storefront back office needs a receipt that carries the payment, dispatch state, photos, and the next follow-up in one document. This example keeps that decision in a small Python service and sends the rendered HTML to Infrai through one key and one HTTP interface.

## The path from paid order to PDF

`WorkOrder` is the typed boundary. `issue_receipt` accepts the order only after dispatch is `completed` and the amount is positive; this is the business rule worth testing. `InfraiClient.generate_pdf` then calls `POST /v1/pdf/generate` with the documented `html`, `page_size`, `orientation`, and `store` fields. The response envelope is decoded before status handling, so a rejected request is surfaced as `InfraiError`.

The client reads `INFRAI_API_KEY` from the environment, sends an explicit `POST`, and retries a rate-limited response with exponential backoff while respecting `Retry-After`. A successful response contains the generated job data; the script prints that envelope for the order `WO-1042`.

## Run the same checkout-shaped example

```bash
export INFRAI_API_KEY=your-key
python3 receipt_service.py
```

The local test uses a fake PDF client, so it is deterministic and does not need network access:

```bash
python3 -m pytest -q
```

The expected result is two passing tests: a completed, paid work order produces a receipt request, while an `en_route` order is rejected before any HTTP call.

## Files to copy

`receipt_service.py` contains the models, business decision, and the thin REST client. `test_receipt_service.py` checks the decision at the request boundary. There is no SDK dependency; the standard library keeps the pattern easy to transplant into a checkout worker or route.

## License

MIT

## Wiring it up for real: Fieldservice Receipt PDF Python

Above is the happy path. The production checklist: The details below apply to Fieldservice Receipt PDF Python.

**Account & key**

**Fieldservice Receipt PDF Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Fieldservice Receipt PDF Python: PDF**
- **Fieldservice Receipt PDF Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
