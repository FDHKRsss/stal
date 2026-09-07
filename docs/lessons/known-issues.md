# Known issues

_Recurring walls/gotchas and how to get past them. One bullet each._

- Flask session cookies: an invalid/tampered signature yields an **empty session** (never a 400), and
  oversized cookies (~4 KB+) are silently dropped by browsers. Treat a bad cookie as an empty cart in both
  code and docs — don't assume Flask raises an error.

- `tests/test_env_and_docs.py` pins the exact `PLAN.md`/`ARCHITECTURE.md` snapshot (milestone checkboxes,
  the "Next action" line, acceptance notes, specific "What's in code" strings). Docs must describe the
  *implemented* state, not the planned state, and code + docs + that snapshot test must land in **one
  commit** (and be committed immediately — uncommitted accepted work gets re-verified as drift). Editing
  docs without the test turns those tests red; merging `-- real` code without the docs leaves the suite
  **green** (the test asserts docs, not code), so only a manual doc-vs-tree diff or the critic catches the
  stale stub docs. (Bit us on M2/M4/M8/M1 -- real, and on M5 -- real — merged at 216 green while
  `cart.py` was still documented as a stub.)

- A `-- real` merge replaces a stub, and stale references to the stub linger beyond the code: the matching
  `tests/test_*_stub.py` must be renamed/rewritten and ARCHITECTURE's "What's in code" test-file list
  updated; *other* tests may pin the stub's transient markers (`test_styling_stub.py` asserted the
  `/oferta/dodaj` flash); and code comments/docstrings can still claim stub behavior (`inject_cart_count`
  said the badge "returns 0 until M5 -- real"). Before marking a stub→real milestone done, grep the whole
  tree for `stub`/old markers and fix them in the same commit.

- A green `pytest -q` does **not** mean the current `-- real` milestone is delivered. Until its stub test is
  replaced, the suite still pins the stub — M3 -- real was reported "green" at 149 tests while
  `tests/test_catalog_stub.py` still asserted `len(PRODUCTS) == 2`. Confirm the real implementation exists
  in the tree before marking it done.

- Routes live in `stal/__init__.py` (the app factory), not a separate `routes.py` and not blueprints —
  earlier notes wrongly treated `routes.py` as a required deliverable. Don't create or expect `routes.py`.
