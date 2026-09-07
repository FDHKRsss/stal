# Project context (durable directives all agents must always honor)

_Seeded from the goal; the architect refined it to the essence._

Build a **very simple Flask** website — a **mock e-shop for steel sales** (screws/bolts, nuts, bars/rods,
angles, flat bars, pipes) — that runs easily on **Windows and Ubuntu**, **no Docker**.

Non-negotiables:

- Flask (Python); runs on Windows + Ubuntu; never Docker.
- **No database, no external services.** Cart lives in the Flask session (signed cookie). Mock only: no real
  payments, orders, stock or warehouse integration.
- Three pages + a mocked confirmation: **homepage** (description + brainstorm about the steel trade),
  **offer** (product/variant/quantity dropdowns, add to cart), **summary** (cart + mocked payment method and
  delivery location).
- Polish UI copy (the demo is for a Polish owner).
- Configurable `HOST`/`PORT`/`SECRET_KEY`/`FLASK_DEBUG` via env with sane defaults; never assume a fixed port
  is free. Env is read from `os.environ` only — no python-dotenv, `.env` is never auto-loaded.
- `README.md` is owned by the goal / human gate — read only; put all plans/design/notes in `docs/`.
- Two-pass build: Pass 1 ships each milestone as a stub (whole app clickable end-to-end); Pass 2 replaces
  each with the real implementation. Stub code is intentional, not unfinished.
- `docs/PLAN.md` + `docs/ARCHITECTURE.md` are pinned by `tests/test_env_and_docs.py` (checkbox state, the
  "Next action" line, acceptance notes, "What's in code" strings): code, docs and that snapshot test must
  ship in **one commit**. A green `pytest -q` only proves the suite passes, **not** that the current
  `-- real` milestone is delivered — the suite pins the stub until `tests/test_*_stub.py` is replaced, and
  real code alone is not done until the docs + snapshot are synced. Confirm the real code **and** the synced
  docs before accepting.
