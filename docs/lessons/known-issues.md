# Known issues

_Recurring walls/gotchas and how to get past them. One bullet each._

- Flask session cookies: an invalid/tampered signature yields an **empty session** (never a 400), and
  oversized cookies (~4 KB+) are silently dropped by browsers. Treat a bad cookie as an empty cart in both
  code and docs — don't assume Flask raises an error.
- Docs must describe the *implemented* (current-pass) behavior, not the planned behavior, and `PLAN.md`
  checkboxes must match accepted work. (Drift seen: `.env.example` claimed env-driven config the stub lacks
  and implied `.env` auto-loading; the M1 checkbox was left unticked despite the work being done.)
- `tests/test_env_and_docs.py` pins the exact `PLAN.md`/`ARCHITECTURE.md` snapshot: milestone checkbox
  state, the "Next action" line, acceptance notes, and a few specific "What's in code" strings
  (`os.environ`/`env-driven`, `404.html` implemented, `routes.py` still missing). Closing a milestone,
  adding an acceptance note, or flipping a file from "not yet" to implemented therefore requires updating
  those doc-state tests and the docs they assert against in the same commit, or the suite fails and blocks
  the milestone. (Bit us on M2 — checkboxes; M4 — `shop.html`; M8 — `style.css`; and M1 -- real — docs still
  held the pre-real snapshot, so 6 tests went red.)
- Pass 2 replaces each stub milestone's matching `tests/test_*_stub.py`, which pins the stub's exact
  copy/markers (e.g. `test_homepage_stub.py` asserted `<title>… (stub)</title>` and the string `stub`).
  Implementing the real version means renaming/rewriting that test (`test_homepage_stub.py` →
  `test_homepage.py`) — not just editing the template — and updating ARCHITECTURE's "What's in code"
  test-file list (which still names the old `*_stub.py`) in the same commit, or the stub test goes red while
  docs drift.
- Commit every accepted milestone in one go (docs + code + the `test_env_and_docs.py` snapshot). Leaving
  accepted work uncommitted in the working tree (as after M8 -- stub, so M9 -- stub + M1 -- real sat there)
  makes later turns re-verify and re-sync already-finished work as if it were drift — wasted effort.
