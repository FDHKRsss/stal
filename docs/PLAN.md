# Plan

## Goal(s)

The north star this plan serves:

1. Build a **very simple Flask web app** — a **mock e-shop for steel sales** (screws/bolts, nuts,
   bars/rods, angles, flat bars, pipes) — that runs easily on **Windows and Ubuntu** and **not** in Docker.
2. Ship the exact buying flow the owner wants to demo:
   - **Homepage** — company description + a brainstorm-style description of the steel trade, including the
     pain of the current "phone + drive + warehouse window + cash register" process and why buying online helps.
   - **Offer page** (shop) — pick a product, a variant (length / quality) and a quantity via dropdowns,
     add to cart.
   - **Summary page** — cart contents + total, plus a **mocked** choice of payment method and delivery location,
     ending on a mocked confirmation.
3. **No database, no external services.** The cart lives in the Flask session (signed cookie). This is a
   presentation mock for the owner, not a functional store (no real payments/orders/stock).

### Non-negotiable constraints (from the goal / human)

- Flask (Python). Runs on Windows + Ubuntu. Never Docker.
- Mock only: no real payments, no real order processing, no real stock/warehouse integration.
- Polish UI copy (the demo is for a Polish owner).
- Sensible port handling: host port configurable via env var with a sane default; never assume a fixed
  host port (e.g. 8000) is free. Env is read from `os.environ` only — no python-dotenv, `.env` is never
  auto-loaded.
- `README.md` is owned by the goal / human gate — read only. All plans/design/notes live in `docs/`.

## Execution order

- **Pass 1 — STUBS:** implement every milestone as a stub/mock so the whole app runs end-to-end
  (all pages reachable, cart "works" with mocked data). Mark each `-- stub` item done.
- **Pass 2 — REAL:** iterate the milestones again and replace each stub with the real implementation.
  Mark each `-- real` item done.
- Order of work within each pass follows M1 → M9. Each milestone is small, individually deliverable and testable.

## Milestones

### M1 — App skeleton & runnable config
- [x] M1 -- stub
- [ ] M1 -- real

Deliverable: `app.py` entry point, `stal/__init__.py` app factory, `stal/config.py`,
`requirements.txt`, `requirements-dev.txt`, `.env.example`, `run.bat` (Windows) and `run.sh` (Ubuntu).
Stub = factory + `app.py` serve `/` and `/health` with fixed text; scripts/venv install/run wired but returning
the stub app. Real = env-driven `HOST` / `PORT` / `SECRET_KEY` / `FLASK_DEBUG` config with sane defaults,
`/health` returning `{"status": "ok"}`, error handlers registered, and working launch scripts.

### M2 — Homepage (description + brainstorm)
- [x] M2 -- stub
- [ ] M2 -- real

Deliverable: `templates/base.html` + `templates/index.html`; GET `/`.
Stub = a plain-text homepage summarizing the company/topic. Real = full Polish copy: company intro, the
current manual buying process, brainstorm about the assortment (screws/bolts, nuts, rods, angles, flat bars,
pipes, lengths 3 m / 6 m, quality variants) and a CTA to the offer page.

### M3 — Product catalog data (mock, no DB)
- [ ] M3 -- stub
- [ ] M3 -- real

Deliverable: `stal/catalog.py` — `PRODUCTS` list + lookup helpers (`get_product`, `get_variant`).
Stub = 2 hardcoded products, one variant each. Real = a realistic catalog of ~8–10 steel products
(fasteners sold per pack of 100; bars/angles/flat bars/pipes sold per sztanga with 3 m / 6 m length and
quality variants), each with `id`, `name`, `category`, `description`, `unit`, and `variants` (id, label, price).

### M4 — Offer / shop page
- [ ] M4 -- stub
- [ ] M4 -- real

Deliverable: `templates/shop.html`; GET `/oferta` + POST `/oferta/dodaj`.
Stub = lists product names; the add-to-cart form posts and redirects with a hardcoded flash. Real = product
cards with a variant dropdown and a quantity dropdown, server-side validation on add, redirect back to
`/oferta` with a success/error flash message.

### M5 — Cart logic (session, no DB)
- [ ] M5 -- stub
- [ ] M5 -- real

Deliverable: `stal/cart.py` — pure helpers over `session`: `get_cart`, `add_item`, `update_item`,
`remove_item`, `clear_cart`, `cart_lines`, `cart_total`.
Stub = functions returning fixed/empty data (no real session). Real = session-backed cart keyed by
`product_id:variant_id`, quantity validation (int, `1..MAX_QTY`), unknown product/variant rejection, merge on
duplicate add, line totals and grand total, and a cart count helper.

### M6 — Summary / checkout page
- [ ] M6 -- stub
- [ ] M6 -- real

Deliverable: `templates/cart.html`; GET `/koszyk` + POST `/koszyk/aktualizuj`.
Stub = static summary with payment/delivery dropdowns that do nothing. Real = renders the real cart lines and
totals, per-line quantity update/remove forms, and the mocked payment-method + delivery-location selectors
(including an address field required when delivery is not "odbiór osobisty").

### M7 — Order confirmation (mocked)
- [ ] M7 -- stub
- [ ] M7 -- real

Deliverable: `templates/confirmation.html`; POST `/zamowienie` (GET redirects to `/koszyk`).
Stub = returns a fixed "zamówienie przyjęte" string. Real = validates non-empty cart + chosen payment +
delivery (+ address when required), shows a mock order number, the items, the chosen payment/delivery and the
total, then clears the cart. Includes a clear "to jest wersja demonstracyjna" note.

### M8 — Styling & UX polish
- [ ] M8 -- stub
- [ ] M8 -- real

Deliverable: `stal/static/style.css`, shared header/nav with cart count, flash messages, footer.
Stub = minimal base template + a bare CSS file (usable but unstyled). Real = clean, presentable, readable
layout (Polish), consistent navigation, cart-count badge, styled product cards, forms and confirmation page —
good enough to show the owner.

### M9 — Tests & robustness
- [ ] M9 -- stub
- [ ] M9 -- real

Deliverable: `tests/test_cart.py`, `tests/test_routes.py`, `tests/conftest.py` (Flask test client).
Stub = one smoke test (app factory creates app; `/health` returns 200). Real = real-behavior tests: cart
add/update/remove/merge/validation, and a full route flow
`/` → `/oferta` → add → `/koszyk` → update → `/zamowienie`, plus error/validation cases. Tests run with
`pytest -q` and use the Flask test client (no fixed port).

## Status & review notes

- No human notes yet.
- 2026-09-07 (critic): "Failure modes considered" previously claimed Flask returns 400 on a bad session
  signature. That was wrong — Flask returns an empty session on `BadSignature` and does not reject oversized
  cookies with 400 (browsers drop them). Corrected in `docs/ARCHITECTURE.md`; plan/milestones unchanged.
- 2026-09-07 (architect): **M1 -- stub accepted** — 23 tests green (`pytest -q`). The stub is static config
  only and `.env.example` truthfully disclaims env auto-loading (env-driven config arrives in `M1 -- real`).
  Committed as the first Pass-1 milestone.
- 2026-09-07 (architect): **M2 -- stub accepted** — 35 tests green (`pytest -q`). `templates/base.html` +
  `templates/index.html` added; GET `/` renders the homepage (Polish stub copy with the steel assortment and
  a "demonstracyjna" note). Plan, "What's in code" and the plan-state tests updated to record it.
- Next action: implement **M3 -- stub**, continuing Pass 1 (all milestones as stubs), then Pass 2 (real),
  committing on each milestone acceptance.
