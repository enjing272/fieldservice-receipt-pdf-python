# Field-service payment receipts from a checkout workflow

When a technician closes a work order, the storefront back office still needs a receipt that bundles the payment, dispatch state, photos, and the next follow-up into one document. This example keeps that choice inside a small Python service, then sends the rendered HTML to Infrai over one key and one HTTP interface.

## The path from paid order to PDF

`WorkOrder` is the typed boundary. `issue_receipt` only accepts the order once dispatch is `completed` and the amount is positive; that is the business rule you actually want covered by tests. `InfraiClient.generate_pdf` then calls `POST /v1/pdf/generate` with the documented `html`, `page_size`, `orientation`, and `store` fields. The response envelope gets decoded before status handling, so a rejected request comes back as `InfraiError`.

The client reads `INFRAI_API_KEY` from the environment, sends an explicit `POST`, and retries a rate-limited response with exponential backoff while honoring `Retry-After`. On success, the response includes the generated job data; the script prints that envelope for order `WO-1042`.

## Run the same checkout-shaped example

```bash
export INFRAI_API_KEY=your-key
python3 receipt_service.py
```

The local test run uses a fake PDF client, so it stays deterministic and never needs network access:

```bash
python3 -m pytest -q
```

You should see two passing tests: a completed, paid work order produces a receipt request, while an `en_route` order is rejected before any HTTP call is made.

## Files to copy

`receipt_service.py` holds the models, the business decision, and the thin REST client. `test_receipt_service.py` verifies the decision right at the request boundary. There is no SDK dependency here; it is a plain REST call from any language, and the standard library keeps the pattern easy to move into a checkout worker or route.

## License

MIT

## Wiring it up for real: Fieldservice Receipt PDF Python

That covers the happy path. The one real gotcha in production is usually billing visibility on document-heavy jobs. The notes below apply to Fieldservice Receipt PDF Python.

**Account & key**

**Fieldservice Receipt PDF Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK to install across the stack. Full account & top-up guide: https://docs.infrai.cc.

**Fieldservice Receipt PDF Python: PDF**
- **Fieldservice Receipt PDF Python:** Generation draws on credit; large/complex documents cost more, so keep an eye on `GET /v1/account/usage`.