# Failures

_Regressions: what broke, the proven root cause, and the fix._

- Working on the wrong milestone wastes the turn and blocks acceptance: a coder re-implemented the
  already-accepted **M6 -- stub** instead of the actually-pending **M7 -- stub** (critic rejected it — no
  forward progress). Proven root cause: coding before reading `PLAN.md`'s milestone checkboxes and the
  "Next action" line, which already marked M6 done and named M7 as next. Fix: before implementing, confirm
  the *currently pending* milestone in `PLAN.md` (checkbox state + "Next action"), and only then write code.
