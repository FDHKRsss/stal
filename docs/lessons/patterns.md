# Patterns

_Reusable techniques that worked, so they are reused not rediscovered._

- When validating a template/stub milestone, test the **rendered** route (status + `text/html` mimetype +
  the expected copy in the response body), not just that the template files exist and `{% extends %}`/block
  wiring is present — that is what catches a route still returning a fixed string instead of `render_template`.
- Build each stub against the fuller spec (`-- real` description + ARCHITECTURE data model), not only the
  terse `-- stub` deliverable line: helpers the real spec requires (e.g. M5's `cart_count`) belong in the
  stub and are correct, not scope drift.
