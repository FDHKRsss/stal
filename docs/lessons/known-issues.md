# Known issues

_Recurring walls/gotchas and how to get past them. One bullet each._

- Flask session cookies: an invalid/tampered signature yields an **empty session** (never a 400), and
  oversized cookies (~4 KB+) are silently dropped by browsers. Treat a bad cookie as an empty cart in both
  code and docs — don't assume Flask raises an error.
- Docs must describe the *implemented* (current-pass) behavior, not the planned behavior, and `PLAN.md`
  checkboxes must match accepted work. (Drift seen: `.env.example` claimed env-driven config the stub lacks
  and implied `.env` auto-loading; the M1 checkbox was left unticked despite the work being done.)
- `tests/test_env_and_docs.py` (renamed from `test_stub_env_and_docs.py`) hard-codes the exact
  `PLAN.md`/`ARCHITECTURE.md` snapshot: milestone checkboxes/status, literal counts like `140 tests green` /
  `140 passing`, **and** the implemented-vs-not-yet-existing file lists. Closing a milestone, changing the
  test count, **or creating a file** the test still lists as "not yet existing" therefore requires updating
  those doc-state tests and the docs they assert against in the same commit, or the suite fails and blocks
  the milestone. (Bit us on M2 — checkboxes/counts; M4 — adding `shop.html`; M8 — creating
  `stal/static/style.css`; and M1 -- real — code already env-driven/`{"status":"ok"}`/with 404-500 handlers
  while docs still held the pre-real snapshot, so 6 tests went red.)
