# Known issues

_Recurring walls/gotchas and how to get past them. One bullet each._

- Flask session cookies: an invalid/tampered signature yields an **empty session** (never a 400), and
  oversized cookies (~4 KB+) are silently dropped by browsers. Treat a bad cookie as an empty cart in both
  code and docs — don't assume Flask raises an error.
- Docs must describe the *implemented* (current-pass) behavior, not the planned behavior, and `PLAN.md`
  checkboxes must match accepted work. (Drift seen: `.env.example` claimed env-driven config the stub lacks
  and implied `.env` auto-loading; the M1 checkbox was left unticked despite the work being done.)
