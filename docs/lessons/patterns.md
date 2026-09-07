# Patterns

_Reusable techniques that worked, so they are reused not rediscovered._

- When validating a template/stub milestone, test the **rendered** route (status + `text/html` mimetype +
  the expected copy in the response body), not just that the template files exist and `{% extends %}`/block
  wiring is present — that is what catches a route still returning a fixed string instead of `render_template`.
- Build each stub against the fuller spec (`-- real` description + ARCHITECTURE data model), not only the
  terse `-- stub` deliverable line: helpers the real spec requires (e.g. M5's `cart_count`) belong in the
  stub and are correct, not scope drift.
- Before writing code to answer a "not delivered / missing" verdict, check **both** the committed state
  (`git log`) *and* the working tree (`git status` + open the file): the work may already be committed
  (stale verdict) or already present uncommitted — in the M9 case the real `tests/test_routes.py` was
  already in the working tree while HEAD still showed the stub, so only the doc/snapshot sync + commit
  remained. Re-implementing either way wastes the turn.
- M9 -- real is a tests-only deliverable, but in this repo test files are **not** reserved to the tester:
  the coder authored/replaced the test suites for M2–M7 -- real and the M9 `tests/test_routes.py`
  route-flow suite. When a milestone's deliverable is test files, the coder writes them too — and always
  syncs `PLAN.md`/`ARCHITECTURE.md` plus the `test_env_and_docs.py` snapshot in the same commit.
