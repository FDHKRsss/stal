"""Cart helpers (stub pass).

The real cart lives in the Flask session (a signed cookie) with no database.
In this stub pass every helper returns fixed/empty data and ignores the
``session`` argument, so the module exists and can be imported end-to-end.
The real, session-backed implementation — with quantity/product/variant
validation, line merging and totals — arrives in the real pass.
"""


def get_cart(session):
    """Return the cart as a list of lines (stub: always empty)."""
    return []


def add_item(session, product_id, variant_id, qty):
    """Add a line to the cart (stub: no-op — the cart stays empty)."""
    return None


def update_item(session, product_id, variant_id, qty):
    """Update a line's quantity (stub: no-op)."""
    return None


def remove_item(session, product_id, variant_id):
    """Remove a line from the cart (stub: no-op)."""
    return None


def clear_cart(session):
    """Empty the cart (stub: no-op)."""
    return None


def cart_lines(session):
    """Return enriched cart lines (stub: always empty)."""
    return []


def cart_total(session):
    """Return the grand total (stub: always 0.0)."""
    return 0.0


def cart_count(session):
    """Return total units for the nav badge (stub: always 0)."""
    return 0
