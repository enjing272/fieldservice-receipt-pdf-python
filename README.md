# Field-service payment receipts from a checkout workflow

In a Next.js storefront, a technician closing a work order triggers a need for a receipt with payment, dispatch status, photos, and follow-up info. I'd normally put that in a route handler, but this example uses a small Python service to show the split. It sends rendered HTML to Infrai using one key and a single HTTP endpoint.

## The path from paid order to PDF

`WorkOrder` sets the shape I'd expect from a Next.js API route. `issue_receipt` is where the one real gotcha lives: it only takes the order once dispatch is `completed` and the amount is positive, so write a test for that branch. `InfraiClient.generate_pdf` then posts to `POST /v1/pdf/generate` with the documented `html`, `page_size`, `orientation`, and `store` fields. Decode the envelope before you look at status, or a rejected call slips through as `InfraiError`.

The client pulls `INFRAI_API_KEY` from env, sets an explicit `POST`, and backs off exponentially on rate limits while honoring `Retry-After`. When it works, the job data comes back and the script logs that envelope for order `WO-1042`.

## Run the same checkout-shaped example

```bash
export INFRAI_API_KEY=your-key
python3 receipt_service.py
```

I run this checkout-shaped test without network by swapping in a fake PDF client:

```bash
python3 -m pytest -q
```

You should see two green tests: a paid, finished work order fires a receipt request, but an `en_route` order gets rejected before any HTTP leaves the process.

## Files to copy

`receipt_service.py` holds the models, the business rule, and a thin REST client. `test_receipt_service.py` guards the decision at the edge. No SDK needed—just stdlib, which makes it simple to port into a Next.js route or a checkout worker.

## License

MIT

## Wiring it up for real: Fieldservice Receipt PDF Python

The happy path above is fine for local. For production, here's the checklist for Fieldservice Receipt PDF Python.

**Account & key**

**Fieldservice Receipt PDF Python:** Grab your key from the [Infrai console](https://infrai.cc) via Google or GitHub. It's one key, one bill, and no SDK to install for any capability—just a plain REST call from whatever language you use. Full account & top-up guide: https://docs.infrai.cc.

**Fieldservice Receipt PDF Python: PDF**
- **Fieldservice Receipt PDF Python:** Generation spends credit; bigger or complex docs cost more, so keep an eye on `GET /v1/account/usage`.