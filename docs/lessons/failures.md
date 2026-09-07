# Failures

_Regressions: what broke, the proven root cause, and the fix._

- Working on the wrong milestone wastes the turn and blocks acceptance: a coder re-implemented the
  already-accepted **M6 -- stub** instead of the actually-pending **M7 -- stub** (critic rejected it — no
  forward progress). Proven root cause: coding before reading `PLAN.md`'s milestone checkboxes and the
  "Next action" line, which already marked M6 done and named M7 as next. Fix: before implementing, confirm
  the *currently pending* milestone in `PLAN.md` (checkbox state + "Next action"), and only then write code.

- **M6 -- real** was rejected despite the code, docs and snapshot test all being synced and the suite green
  (250 passing), because the milestone was never **committed**: `git log` still ended at the M7 -- real
  commit and the M6 files sat modified/untracked in the working tree, so the committed state the reviewer
  checks still showed the stale pre-M6 docs (`- [ ] M6 -- real`, "summary stub", `test_cart_page_stub.py`).
  Proven root cause: declaring "done" on working-tree state instead of a committed milestone. Fix: land code
  + synced `PLAN.md`/`ARCHITECTURE.md` + the snapshot test in ONE commit before accepting the milestone.
