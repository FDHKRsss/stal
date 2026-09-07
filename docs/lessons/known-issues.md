# Known issues

_Recurring walls/gotchas and how to get past them. One bullet each._

- Flask session cookies: an invalid/tampered signature yields an **empty session** (never a 400), and
  oversized cookies (~4 KB+) are silently dropped by browsers. Treat a bad cookie as an empty cart in both
  code and docs — don't assume Flask raises an error.
- Docs must describe the *implemented* (current-pass) behavior, not the planned behavior, and `PLAN.md`
  checkboxes must match accepted work. (Drift seen: `.env.example` claimed env-driven config the stub lacks
  and implied `.env` auto-loading; the M1 checkbox was left unticked despite the work being done.)
- `tests/test_stub_env_and_docs.py` hard-codes the exact `PLAN.md`/`ARCHITECTURE.md` snapshot: milestone
  checkboxes/status **and** literal counts like `35 tests green` / `35 passing`. Closing a milestone **or**
  changing the number of test functions therefore requires updating those doc-state tests (and the docs they
  assert against) in the same commit, or the suite fails and blocks the milestone. (Bit us on M2: marking it
  done broke two plan-state assertions; a later `30→35` count drift was flagged as cosmetic and then pinned
  in the tests.)
