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
- [x] M1 -- real

Deliverable: `app.py` entry point, `stal/__init__.py` app factory, `stal/config.py`,
`requirements.txt`, `requirements-dev.txt`, `.env.example`, `run.bat` (Windows) and `run.sh` (Ubuntu).
Stub = factory + `app.py` serve `/` and `/health` with fixed text; scripts/venv install/run wired but returning
the stub app. Real = env-driven `HOST` / `PORT` / `SECRET_KEY` / `FLASK_DEBUG` config with sane defaults,
`/health` returning `{"status": "ok"}`, error handlers registered, and working launch scripts.

### M2 — Homepage (description + brainstorm)
- [x] M2 -- stub
- [x] M2 -- real

Deliverable: `templates/base.html` + `templates/index.html`; GET `/`.
Stub = a plain-text homepage summarizing the company/topic. Real = full Polish copy: company intro, the
current manual buying process, brainstorm about the assortment (screws/bolts, nuts, rods, angles, flat bars,
pipes, lengths 3 m / 6 m, quality variants) and a CTA to the offer page.

### M3 — Product catalog data (mock, no DB)
- [x] M3 -- stub
- [x] M3 -- real

Deliverable: `stal/catalog.py` — `PRODUCTS` list + lookup helpers (`get_product`, `get_variant`).
Stub = 2 hardcoded products, one variant each. Real = a realistic catalog of ~8–10 steel products
(fasteners sold per pack of 100; bars/angles/flat bars/pipes sold per sztanga with 3 m / 6 m length and
quality variants), each with `id`, `name`, `category`, `description`, `unit`, and `variants` (id, label, price).

### M4 — Offer / shop page
- [x] M4 -- stub
- [x] M4 -- real

Deliverable: `templates/shop.html`; GET `/oferta` + POST `/oferta/dodaj`.
Stub = lists product names; the add-to-cart form posts and redirects with a hardcoded flash. Real = product
cards with a variant dropdown and a quantity dropdown, server-side validation on add, redirect back to
`/oferta` with a success/error flash message.

### M5 — Cart logic (session, no DB)
- [x] M5 -- stub
- [x] M5 -- real

Deliverable: `stal/cart.py` — pure helpers over `session`: `get_cart`, `add_item`, `update_item`,
`remove_item`, `clear_cart`, `cart_lines`, `cart_total`.
Stub = functions returning fixed/empty data (no real session). Real = session-backed cart keyed by
`product_id:variant_id`, quantity validation (int, `1..MAX_QTY`), unknown product/variant rejection, merge on
duplicate add, line totals and grand total, and a cart count helper.

### M6 — Summary / checkout page
- [x] M6 -- stub
- [~] M6 -- real

Deliverable: `templates/cart.html`; GET `/koszyk` + POST `/koszyk/aktualizuj`.
Stub = static summary with payment/delivery dropdowns that do nothing. Real = renders the real cart lines and
totals, per-line quantity update/remove forms, and the mocked payment-method + delivery-location selectors
(including an address field required when delivery is not "odbiór osobisty").

### M7 — Order confirmation (mocked)
- [x] M7 -- stub
- [x] M7 -- real

Deliverable: `templates/confirmation.html`; POST `/zamowienie` (GET redirects to `/koszyk`).
Stub = returns a fixed "zamówienie przyjęte" string. Real = validates non-empty cart + chosen payment +
delivery (+ address when required), shows a mock order number, the items, the chosen payment/delivery and the
total, then clears the cart. Includes a clear "to jest wersja demonstracyjna" note.

### M8 — Styling & UX polish
- [x] M8 -- stub
- [ ] M8 -- real

Deliverable: `stal/static/style.css`, shared header/nav with cart count, flash messages, footer.
Stub = minimal base template + a bare CSS file (usable but unstyled). Real = clean, presentable, readable
layout (Polish), consistent navigation, cart-count badge, styled product cards, forms and confirmation page —
good enough to show the owner.

### M9 — Tests & robustness
- [x] M9 -- stub
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
- 2026-09-07 (architect): **M3 -- stub accepted** — 49 tests green (`pytest -q`). `stal/catalog.py` +
  `tests/test_catalog_stub.py` added (2 hardcoded products, one variant each; `get_product`/`get_variant`
  raise `KeyError`). Plan, "What's in code" and the plan-state tests updated to record it.
- 2026-09-07 (architect): **M4 -- stub accepted** — 65 tests green (`pytest -q`). `templates/shop.html`
  added; GET `/oferta` renders the offer stub (each product's name + unit with a per-product "Dodaj do
  koszyka" form posting to `/oferta/dodaj`) and POST `/oferta/dodaj` flashes a fixed demo message then
  redirects back to `/oferta`. Plan, "What's in code" and the plan-state tests updated to record it.
- 2026-09-07 (architect): **M5 -- stub accepted** — 78 tests green (`pytest -q`). `stal/cart.py` added
  with the full cart API as stubs (`get_cart`, `add_item`, `update_item`, `remove_item`, `clear_cart`,
  `cart_lines`, `cart_total`, `cart_count`) returning fixed/empty data and ignoring the `session`
  argument (no real session logic). Plan, "What's in code" and the plan-state tests updated to record it.
- 2026-09-07 (architect): **M6 -- stub accepted** — 102 tests green (`pytest -q`). `stal/templates/cart.html`
  added; GET `/koszyk` renders the summary stub (empty-cart note + `0,00 zł` total, mocked payment-method
  radios and delivery `<select>` plus an address field) and POST `/koszyk/aktualizuj` flashes a fixed demo
  message then redirects back to `/koszyk`. Plan, "What's in code" and the plan-state tests updated to
  record it.
- 2026-09-07 (architect): **M7 -- stub accepted** — 119 tests green (`pytest -q`). `stal/templates/confirmation.html`
  added; POST `/zamowienie` renders the static mocked confirmation ("Zamówienie przyjęte", demo order number
  `ZAM-DEMO-0001`, `0,00 zł` total and a link back to the homepage) and GET `/zamowienie` redirects to
  `/koszyk`; the cart page now posts a "Złóż zamówienie" form to `/zamowienie`. Plan, "What's in code" and
  the plan-state tests updated to record it.
- 2026-09-07 (tester): **M8 -- stub accepted** — 133 tests green (`pytest -q`). Added
  `stal/static/style.css` and reworked `stal/templates/base.html` with a shared header/nav (brand +
  Oferta + Koszyk with a `cart-count` badge), flash rendering and a footer; `create_app()` now injects
  `cart_count` via a context processor (returns `0` in the stub). Plan, "What's in code" and the
  plan-state tests updated to record it.
- 2026-09-07 (tester): **M9 -- stub accepted** — 135 tests green (`pytest -q`). Added
  `tests/test_cart.py` and `tests/test_routes.py` as stub smoke tests (the cart module is wired
  end-to-end; the app factory creates a Flask app and `/health` answers 200 through the test client).
  `tests/conftest.py` already provided the `app`/`client` fixtures. Plan, "What's in code" and the
  plan-state tests updated to record it.
- 2026-09-07 (tester): **M1 -- real accepted** — 140 tests green (`pytest -q`). `stal/config.py` is now
  env-driven (reads `HOST`/`PORT`/`SECRET_KEY`/`FLASK_DEBUG` from `os.environ`, no dotenv/`.env`
  auto-loading), `/health` returns `{"status":"ok"}`, 404/500 error handlers are registered, and the
  launch scripts run the real config. `tests/test_env_and_docs.py` and the doc state updated to match.
- 2026-09-07 (architect): committed **M9 -- stub** + **M1 -- real** together (140 tests green).
  All Pass-1 stubs are now complete; Pass 2 continues with M2 -- real.
- 2026-09-07 (coder): **M2 -- real accepted** — 149 tests green (`pytest -q`).
  `stal/templates/index.html` now carries the full Polish homepage copy (company intro, the steel
  assortment with lengths 3 m / 6 m and quality variants, the current manual buying process, why buying
  online helps and a CTA to `/oferta`). `tests/test_homepage.py` replaces `tests/test_homepage_stub.py`,
  and `tests/test_skeleton.py` now asserts the real copy. Plan, "What's in code" and the plan-state tests
  updated to record it.
- 2026-09-07 (architect): **M3 -- real not delivered this round** — `stal/catalog.py` is still the
  2-product stub, `stal/routes.py` is still missing and the working tree is unchanged since the
  M2 -- real commit. The 149 green tests are the *stub* suite (they do not exercise M3 -- real).
  Keeping `- [ ] M3 -- real` and re-queueing it as a small, unblocked task rather than parking it.
- 2026-09-07 (coder): **M3 -- real accepted** — 161 tests green (`pytest -q`). `stal/catalog.py` now
  carries the real catalog of 9 steel products (4 fasteners sold per `opak. 100 szt.` with
  `ocynkowana`/`nierdzewna A2` variants; 5 profiles sold per `sztanga` with 3 m / 6 m lengths and
  `S235JR`/`nierdzewna` quality) plus `get_product`/`get_variant` raising `KeyError` on unknown ids.
  `tests/test_catalog.py` replaces `tests/test_catalog_stub.py`. Plan, "What's in code" and the
  plan-state tests updated to record it.
- 2026-09-07 (coder): **M4 -- real accepted** — 177 tests green (`pytest -q`). GET `/oferta` now
  renders the real offer (`templates/shop.html`): one product card per catalog item with a variant
  dropdown (label + price) and a quantity dropdown (`1..MAX_QTY`); POST `/oferta/dodaj` validates
  `product_id`/`variant_id`/`qty` server-side and flashes a Polish success/error message before
  redirecting back to `/oferta`. `tests/test_offer.py` replaces `tests/test_offer_stub.py`. Plan,
  "What's in code" and the plan-state tests updated to record it.
- 2026-09-07 (architect): committed **M4 -- real** (177 tests green). Reconciled the `routes.py`
  design drift in ARCHITECTURE: routes live in `stal/__init__.py` (no separate `routes.py`).
- 2026-09-07 (coder): **M5 -- real accepted** — 220 tests green (`pytest -q`). `stal/cart.py` now
  implements the real session-backed cart (`get_cart`, `add_item`, `update_item`, `remove_item`,
  `clear_cart`, `cart_lines`, `cart_total`, `cart_count`) with quantity validation (int, `1..MAX_QTY`),
  unknown product/variant rejection, merge-on-duplicate capped at `MAX_QTY`, line totals and the
  nav-badge unit count; `POST /oferta/dodaj` and the shared nav badge now use the real helper.
  `tests/test_cart.py` replaces `tests/test_cart_stub.py`. Plan, "What's in code" and the
  plan-state tests updated to record it.
- 2026-09-07 (architect): committed **M5 -- real** (220 tests green) — the cart implementation,
  its tests and the doc/test updates had been left uncommitted after acceptance; recorded as
  `milestone: M5 cart logic (real)`.
- 2026-09-07 (architect): **M6 -- real not delivered this round** — the coder reported green, but
  `stal/templates/cart.html` and the `GET /koszyk` / `POST /koszyk/aktualizuj` routes are still the
  M6 stub and `tests/test_cart_page_stub.py` still pins the stub (the 220 green tests are the stub
  suite, not M6 -- real). Parking `M6 -- real` as `- [~]` so the coder moves on to M7 instead of
  re-trying the same stuck item.
- 2026-09-07 (coder): **M7 -- real accepted** — 234 tests green (`pytest -q`). `stal/__init__.py` now
  implements the real `POST /zamowienie` (validates a non-empty cart, a known payment method, a known
  delivery location and an address when required; generates a `ZAM-YYYYMMDD-HHMMSS` order number;
  renders the live items/total and the chosen payment/delivery; then clears the cart) and
  `stal/templates/confirmation.html` renders that validated, clearly-demo confirmation.
  `tests/test_confirmation.py` replaces `tests/test_confirmation_stub.py`. Plan, "What's in code" and
  the plan-state tests updated to record it.
- Next action: implement **M8 -- real** (M6 -- real remains parked), committing on each
  milestone acceptance.
