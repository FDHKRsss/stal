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
- Configurable host port via env (sane default); never assume a fixed port is free.
- `README.md` is owned by the goal / human gate — read only; put all plans/design/notes in `docs/`.
