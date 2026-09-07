# Architecture

## Overview

A tiny Flask application that is a **mock e-shop for steel sales** (screws/bolts, nuts, bars/rods, angles,
flat bars, pipes). It is meant to be shown to the shop owner, so it must:

- run easily on **Windows and Ubuntu** (no Docker),
- have **no database** and no external services,
- provide a realistic, clickable flow: homepage → offer → summary (payment + delivery) → mocked confirmation.

The cart is stored in the **Flask session** (a signed cookie), which is the smallest possible "state" that
needs no server storage and no database. All product data is static Python data in `catalog.py`.

## Decisions & trade-offs

| Decision | Chosen | Why / rejected alternative |
|---|---|---|
| Framework | **Flask** (Python) | Explicitly requested; tiny, cross-platform, no Docker. |
| Rendering | **Jinja2 templates** (bundled with Flask) | No extra dependency; enough for a 4-page mock. |
| Database | **None** — Flask session (signed cookie) | The owner explicitly wants a mock, not a functional store. Server-side DBs, SQLite, and even JSON-file persistence were rejected as unnecessary complexity. Cookie size is fine for a small demo cart. |
| Form handling | **Plain HTML forms + manual validation** in `cart.py`/routes | Avoids Flask-WTF/WTForms dependency. The few inputs (variant, quantity, payment, delivery, address) are easy to validate by hand. CSRF is intentionally out of scope for a non-auth demo. |
| App structure | **App factory** (`create_app`) + thin `app.py` entry | Factory makes the app testable (Flask test client) and keeps config/route registration clean. A single-file app was rejected because catalog/cart logic benefits from separation for testing. |
| Routes | One `routes.py` module (no blueprints) | Only ~6 endpoints; blueprints add ceremony with no benefit here. |
| Product model | Flat `variants` list per product | A single "variant" dropdown whose label encodes length/quality (e.g. `6 m · S235JR`) is simpler and less error-prone than separate length+quality dropdowns with derived pricing, while still demonstrating the length/quality concept the owner described. |
| Pricing | Hardcoded prices per variant | Real, believable numbers for the demo; no pricing math to get wrong. |
| Config | Env vars with defaults (`HOST`, `PORT`, `SECRET_KEY`, `FLASK_DEBUG`) | Port is configurable and defaults to a sensible value; the app never assumes a fixed port is free. |

## Project layout

```
.
├── app.py                 # entry point: app = create_app(); app.run(...)
├── requirements.txt       # runtime: Flask
├── requirements-dev.txt   # -r requirements.txt + pytest
├── .env.example           # documented HOST / PORT / SECRET_KEY / FLASK_DEBUG
├── run.bat                # Windows launcher (create venv if missing, install, run)
├── run.sh                 # Ubuntu/macOS launcher (same, POSIX sh)
├── stal/
│   ├── __init__.py        # create_app(): config, error handlers, route registration
│   ├── config.py          # Config (reads env; defaults)
│   ├── catalog.py         # PRODUCTS mock data + get_product/get_variant
│   ├── cart.py            # pure cart helpers + validation (over Flask session)
│   ├── routes.py          # all routes: /, /oferta, /oferta/dodaj, /koszyk, /koszyk/aktualizuj, /zamowienie, /health
│   ├── templates/
│   │   ├── base.html      # layout: header/nav (cart count), flash messages, footer
│   │   ├── index.html     # homepage: description + brainstorm + CTA
│   │   ├── shop.html      # offer: product cards with variant + quantity dropdowns
│   │   ├── cart.html      # summary: cart lines + totals + payment/delivery choice
│   │   ├── confirmation.html  # mocked order confirmation
│   │   └── 404.html       # friendly not-found
│   └── static/
│       └── style.css      # single stylesheet
└── tests/
    ├── conftest.py        # app/test client fixture
    ├── test_cart.py       # cart logic tests
    └── test_routes.py     # route-flow + validation tests
```

## Data model

### Catalog (`stal/catalog.py`)

`PRODUCTS` is a list of dicts. Each product:

```python
{
  "id": "katownik-40x40x4",          # slug, unique
  "name": "Kątownik 40×40×4 mm",
  "category": "Kształtowniki",
  "description": "…",                 # short Polish description
  "unit": "sztanga",                  # "sztanga" for bars/angles/flat bars/pipes; "opak. 100 szt." for fasteners
  "variants": [
    {"id": "3m-s235jr", "label": "3 m · S235JR", "price": 62.00},
    {"id": "6m-s235jr", "label": "6 m · S235JR", "price": 124.00},
  ],
}
```

Lookup helpers raise `KeyError` on unknown ids so callers get a clear signal to convert into a user-facing error.

### Cart (`stal/cart.py`)

Session key `"cart"` holds a list of lines (order-preserving):

```python
[{"product_id": "katownik-40x40x4", "variant_id": "3m-s235jr", "qty": 2}, …]
```

- `add_item` merges quantities when `(product_id, variant_id)` already exists.
- `update_item` sets `qty`; `qty <= 0` removes the line.
- `cart_lines` enriches lines with product/variant data and computes `line_total`; `cart_total` sums them.
- `cart_count` returns total units for the nav badge.
- `MAX_QTY = 99`; quantities must be integers in `1..MAX_QTY`.

## Routes & flow

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Homepage (description + brainstorm + CTA to `/oferta`). |
| GET | `/oferta` | Offer page: product cards with variant + quantity dropdowns. |
| POST | `/oferta/dodaj` | Validate and add to cart; redirect to `/oferta` with flash. |
| GET | `/koszyk` | Summary: cart lines, totals, payment + delivery choice. |
| POST | `/koszyk/aktualizuj` | Update a line's quantity or remove it. |
| POST | `/zamowienie` | Validate + show mocked confirmation, then clear the cart. |
| GET | `/health` | `{"status":"ok"}` for cheap environment checks. |

Payment methods (mocked, radios): przelew bankowy (przedpłata), karta płatnicza online, gotówka przy odbiorze,
przelew z odroczonym terminem (dla firm).

Delivery locations (mocked, select): odbiór osobisty (magazyn), dostawa kurierem, dostawa transportem własnym.
An address text field is shown and **required unless** "odbiór osobisty" is chosen.

## Validation & error handling

- All POST inputs are read from `request.form` and validated server-side; client controls are just UX.
  - `product_id` / `variant_id` must exist in the catalog (reject otherwise with a Polish flash).
  - `qty` must be an int in `1..MAX_QTY`.
  - `zamowienie` requires a non-empty cart, a known payment method, a known delivery location, and an address
    when delivery ≠ odbiór osobisty.
- Invalid inputs never crash: they flash a Polish message and redirect back to the originating page.
- 404 → `404.html`; 500 → a safe "Wystąpił błąd serwera." response (no stack traces in the demo).
- The mock order number is generated deterministically from the server clock (e.g. `ZAM-YYYYMMDD-HHMMSS`),
  clearly marked as demo.

## Configuration & port handling

`stal/config.py` reads environment variables with defaults:

| Var | Default | Meaning |
|---|---|---|
| `HOST` | `127.0.0.1` | Bind address (set `0.0.0.0` to expose on a LAN). |
| `PORT` | `5000` | Host port. Configurable because the default may be occupied. |
| `SECRET_KEY` | dev-only fallback | Session signing key; override in real use. |
| `FLASK_DEBUG` | `0` | `1` enables debug mode. |

The app only binds a concrete port when launched via `app.py` / `run.bat` / `run.sh`. Tests use the Flask
test client (no port bound), so they never depend on a free port.

## Run instructions (owner-friendly)

Windows:

```
run.bat
```

Ubuntu:

```
./run.sh
```

Both scripts: create `.venv` if missing → activate → `pip install -r requirements.txt` → `python app.py`.
Manual equivalent: `python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && python app.py`
(Windows uses `.venv\Scripts\activate`).

## Testing strategy

- `tests/test_cart.py`: pure-unit tests for add/merge/update/remove/clear/totals and quantity/product/variant
  validation.
- `tests/test_routes.py`: full user flow with the Flask test client, plus validation and 404/redirect cases.
- Run with `pytest -q` (uses `requirements-dev.txt`). No tests assert against a fixed host port.

## Failure modes considered

- **Port already in use** → configurable `PORT`; clear startup error remains visible (do not silently retry).
- **Missing/empty `SECRET_KEY`** → dev fallback key + note to override; session works for the demo.
- **Tampered / invalid session cookie** → Flask's `SecureCookieSessionInterface.open_session` catches
  `BadSignature` and returns an **empty session** (never a 400), so a tampered cookie behaves like an empty
  cart. Cart helpers additionally never trust client-supplied product/variant ids and re-validate them
  against the catalog.
- **Oversized cookie** → Flask does **not** reject it with 400; browsers silently drop cookies over ~4 KB.
  The demo cart is tiny, so this is not a real risk. (If it ever became one, server-side storage would be
  required, which is out of scope for this mock.)
- **Unknown product/variant or bad quantity** → friendly flash + redirect, no crash.
- **Missing dependencies** → launcher installs `requirements.txt`; tests install `requirements-dev.txt`.

## Review notes

- 2026-09-07 (critic): corrected the "failure modes" bullet that claimed Flask returns 400 on a bad session
  signature. Flask actually returns an empty session on `BadSignature`, and it does not reject oversized
  cookies with 400 — browsers drop them. Docs updated to state the real behavior; the rest of the design is
  unchanged.
- 2026-09-07 (architect): accepted **M1 -- stub** (23 tests green). Updated "What's in code" so docs describe
  the implemented stub rather than the planned state.
- 2026-09-07 (architect): accepted **M2 -- stub** (35 tests green). `/` now renders `templates/index.html`;
  updated "What's in code" to record M2 -- stub and the new template files.
- 2026-09-07 (architect): accepted **M3 -- stub** (49 tests green). Added `stal/catalog.py` (2 hardcoded
  products, one variant each; `get_product`/`get_variant` raise `KeyError`) and `tests/test_catalog_stub.py`;
  "What's in code" updated.
- 2026-09-07 (tester): **M4 -- stub implemented.** `/oferta` renders `templates/shop.html`
  (product names + units, per-product "Dodaj do koszyka" form) and `POST /oferta/dodaj` flashes a fixed demo
  message and redirects back to `/oferta`; `base.html` now renders flash messages and `index.html` links to
  `/oferta`. "What's in code" and the doc-state tests updated to match.
- 2026-09-07 (architect): accepted **M4 -- stub** (65 tests green). `/oferta` renders `shop.html` with a
  per-product add-to-cart form, and `POST /oferta/dodaj` flashes a fixed demo message then redirects back.
  "What's in code" updated to record M4 -- stub as accepted.
- 2026-09-07 (architect): accepted **M5 -- stub** (78 tests green). `stal/cart.py` exposes the full cart
  API as stubs (`get_cart`, `add_item`, `update_item`, `remove_item`, `clear_cart`, `cart_lines`,
  `cart_total`, `cart_count`) returning fixed/empty data and ignoring the `session` argument (no real
  session logic). "What's in code" and the plan-state tests updated to record it.
- 2026-09-07 (architect): accepted **M6 -- stub** (102 tests green). `stal/templates/cart.html` added;
  GET `/koszyk` renders the summary stub (empty-cart note + `0,00 zł` total, mocked payment-method radios
  and delivery `<select>` plus an address field) and POST `/koszyk/aktualizuj` flashes a fixed demo message
  then redirects back to `/koszyk`. "What's in code" updated to record M6 -- stub as accepted.
- 2026-09-07 (architect): accepted **M7 -- stub** (119 tests green). `stal/templates/confirmation.html` added;
  POST `/zamowienie` renders the static mocked confirmation and GET `/zamowienie` redirects to `/koszyk`;
  the cart page now posts a "Złóż zamówienie" form to `/zamowienie`. "What's in code" updated to record
  M7 -- stub as accepted.
- 2026-09-07 (tester): accepted **M8 -- stub** (133 tests green). Added `stal/static/style.css` and reworked
  `base.html` with a shared header/nav (brand + Oferta + Koszyk with a `cart-count` badge), flash rendering
  and a footer; `create_app()` injects `cart_count` via a context processor (returns `0` in the stub).
  "What's in code" and the doc-state tests updated to match.

- 2026-09-07 (tester): accepted **M9 -- stub** (135 tests green). Added `tests/test_cart.py` and
  `tests/test_routes.py` as stub smoke tests (the cart module is wired end-to-end; the app factory creates
  a Flask app and `/health` answers 200 via the test client); `tests/conftest.py` already provided the
  fixtures. "What's in code" and the doc-state tests updated to match.

- 2026-09-07 (tester): accepted **M1 -- real** (140 tests green). `stal/config.py` is now env-driven
  (reads `HOST`/`PORT`/`SECRET_KEY`/`FLASK_DEBUG` from `os.environ` with sane defaults; no dotenv/`.env`
  auto-loading), `/health` returns `{"status":"ok"}`, and 404/500 error handlers are registered. "What's in
  code" and the doc-state tests updated to record the real config.

- 2026-09-07 (architect): committed M9 -- stub and M1 -- real (140 tests green).

## What's in code (stubs vs real) — current status

- **Implemented so far (Pass 1):** `M1 -- stub`, `M2 -- stub`, `M3 -- stub`, `M4 -- stub`, `M5 -- stub`,
  `M6 -- stub`, `M7 -- stub`, `M8 -- stub` and `M9 -- stub`.
- **Implemented so far (Pass 2):** `M1 -- real`.
  - `app.py` — entry point (`app = create_app()`; `app.run(...)` guarded by `__main__`).
  - `stal/__init__.py` — `create_app()` with eight routes: `/` renders `index.html` (homepage stub),
    `/oferta` renders `shop.html` (offer stub), `POST /oferta/dodaj` flashes a fixed demo message and
    redirects to `/oferta`, `GET /koszyk` renders `cart.html` (summary stub),
    `POST /koszyk/aktualizuj` flashes a fixed demo message and redirects to `/koszyk`,
    `GET /zamowienie` redirects to `/koszyk`, `POST /zamowienie` renders `confirmation.html`
    (mocked confirmation), and `/health` returns `{"status": "ok"}`; a context processor injects `cart_count`
    (from `stal.cart.cart_count`, `0` in the stub) for the shared nav badge. 404/500 error handlers are
    registered (404 → `404.html`, 500 → a safe Polish message).
  - `stal/config.py` — env-driven `Config` reading `HOST`/`PORT`/`SECRET_KEY`/`FLASK_DEBUG` from
    `os.environ` with sane defaults; no dotenv/`.env` auto-loading.
  - `stal/catalog.py` — mock catalog: 2 hardcoded products, one variant each; `get_product`/`get_variant`
    raise `KeyError` on unknown ids.
  - `stal/cart.py` — cart helpers (stub): `get_cart`, `add_item`, `update_item`, `remove_item`,
    `clear_cart`, `cart_lines`, `cart_total` and `cart_count` all return fixed/empty data and ignore the
    `session` argument (no real session logic).
  - `stal/templates/base.html` — Polish layout shell (`<html lang="pl">`, `title` + `content` blocks) with
    a shared header/nav (brand + Oferta + Koszyk with a `cart-count` badge), flash rendering, a stylesheet
    link to `/static/style.css` and a footer.
  - `stal/templates/index.html` — homepage stub (extends `base.html`): a short Polish intro listing the
    assortment (śruby, nakrętki, pręty, kątowniki, płaskowniki, rury), clearly marked as demo/stub, with a
    CTA link to `/oferta`.
  - `stal/templates/shop.html` — offer stub (extends `base.html`): lists each catalog product's name + unit
    with a per-product "Dodaj do koszyka" form posting to `/oferta/dodaj`.
  - `stal/templates/cart.html` — summary stub (extends `base.html`): an empty-cart note with a `0,00 zł`
    total, mocked payment-method radios (przelew / karta / gotówka / odroczony termin), a mocked delivery
    `<select>` (odbiór osobisty / kurier / transport własny) plus an address field, an "Zaktualizuj
    koszyk" form posting to `update_cart`, a "Złóż zamówienie" form posting to `place_order`, and a link
    back to the offer.
  - `stal/templates/confirmation.html` — mocked order confirmation (extends `base.html`): a static
    "Zamówienie przyjęte" heading, a demo order number `ZAM-DEMO-0001`, a `0,00 zł` total and a link back
    to the homepage.
  - `stal/templates/404.html` — friendly Polish not-found page (rendered by the registered 404 handler).
  - `stal/static/style.css` — a bare, usable stylesheet for the header/nav, main area, flash messages and
    footer.
  - `requirements.txt` (`Flask>=3.0`), `requirements-dev.txt` (`-r requirements.txt` + `pytest`),
    `pytest.ini`, `.env.example` (documents config vars and explicitly disclaims env auto-loading),
    `run.bat` / `run.sh` (create `.venv` if missing, install, run `python app.py`).
  - `tests/test_cart.py` — stub smoke test: `stal.cart` exposes the full documented API and its readers
    return the fixed/empty stub values.
  - `tests/test_routes.py` — stub smoke test: `create_app()` builds a Flask app and `/health` answers 200
    through the Flask test client.
  - Tests: `tests/conftest.py`, `tests/test_skeleton.py`, `tests/test_env_and_docs.py`,
    `tests/test_homepage_stub.py`, `tests/test_catalog_stub.py`, `tests/test_offer_stub.py`,
    `tests/test_cart_stub.py`, `tests/test_cart_page_stub.py`, `tests/test_confirmation_stub.py`,
    `tests/test_styling_stub.py`, `tests/test_cart.py`, `tests/test_routes.py` — **140 passing**.
- **Not implemented yet (still to do in Pass 2):** `routes.py` does not exist yet; it is described above as
  the real-pass design.

Pass 1 rule: implement every milestone as a stub so the whole app runs end-to-end before Pass 2 replaces
each stub with the real implementation described in this document.
