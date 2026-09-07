"""Session-backed cart helpers (real pass).

The cart lives in the Flask session under the key ``"cart"`` as an
order-preserving list of lines::

    [{"product_id": "katownik-40x40x4", "variant_id": "3m-s235jr", "qty": 2}, …]

No database and no external services are involved. Every helper takes the
Flask ``session`` (any mutable mapping, e.g. a plain ``dict`` in tests) as its
first argument.

Client-supplied product/variant ids are re-validated against ``stal.catalog``
on add, so a tampered or stale session can never build a line for a product the
catalog does not know. Quantity validation enforces integers in ``1..MAX_QTY``
for added quantities; ``update_item`` treats ``qty <= 0`` as a removal.
"""

from stal.catalog import get_product, get_variant

MAX_QTY = 99
_CART_KEY = "cart"


# --- internal helpers ------------------------------------------------------


def _coerce_qty(qty):
    """Return ``qty`` as an int or raise ``ValueError`` when it is not one.

    ``bool`` is a subclass of ``int`` in Python, but it is never a meaningful
    quantity, so it is rejected explicitly.
    """
    if isinstance(qty, bool) or not isinstance(qty, int):
        raise ValueError("Ilość musi być liczbą całkowitą.")
    return qty


def _raw_cart(session):
    """Return the mutable cart list held in ``session``, creating it if needed."""
    cart = session.get(_CART_KEY)
    if cart is None:
        cart = []
        session[_CART_KEY] = cart
    return cart


# --- public API ------------------------------------------------------------


def get_cart(session):
    """Return the cart as a list of line dicts (fresh copies)."""
    return [dict(line) for line in session.get(_CART_KEY, [])]


def add_item(session, product_id, variant_id, qty):
    """Add ``qty`` units of a product/variant to the cart.

    Validates the quantity (an int in ``1..MAX_QTY``) and that the
    product/variant exists in the catalog; invalid input raises ``ValueError``
    or ``KeyError`` respectively and leaves the session untouched.

    Adding a line that already exists merges the quantities; the merged total
    is capped at ``MAX_QTY`` so a line can never exceed the documented maximum.
    """
    qty = _coerce_qty(qty)
    if qty < 1 or qty > MAX_QTY:
        raise ValueError(f"Ilość musi być liczbą od 1 do {MAX_QTY}.")

    # Re-validate against the catalog; raises KeyError on unknown ids.
    get_variant(product_id, variant_id)

    cart = _raw_cart(session)
    for line in cart:
        if line["product_id"] == product_id and line["variant_id"] == variant_id:
            line["qty"] = min(line["qty"] + qty, MAX_QTY)
            session[_CART_KEY] = cart
            return None

    cart.append({"product_id": product_id, "variant_id": variant_id, "qty": qty})
    session[_CART_KEY] = cart
    return None


def update_item(session, product_id, variant_id, qty):
    """Set the quantity of an existing line, or remove it for ``qty <= 0``.

    Non-integer quantities raise ``ValueError``; a positive quantity above
    ``MAX_QTY`` is rejected with ``ValueError``. If no matching line exists the
    call is a no-op.
    """
    qty = _coerce_qty(qty)

    cart = session.get(_CART_KEY)
    if not cart:
        return None

    for line in cart:
        if line["product_id"] == product_id and line["variant_id"] == variant_id:
            if qty <= 0:
                cart.remove(line)
            elif qty > MAX_QTY:
                raise ValueError(f"Ilość musi być liczbą od 1 do {MAX_QTY}.")
            else:
                line["qty"] = qty
            session[_CART_KEY] = cart
            return None

    return None


def remove_item(session, product_id, variant_id):
    """Remove a line from the cart (a no-op when it is not present)."""
    cart = session.get(_CART_KEY)
    if not cart:
        return None

    for line in list(cart):
        if line["product_id"] == product_id and line["variant_id"] == variant_id:
            cart.remove(line)

    session[_CART_KEY] = cart
    return None


def clear_cart(session):
    """Empty the cart."""
    session[_CART_KEY] = []
    return None


def cart_lines(session):
    """Return enriched cart lines with product/variant data and ``line_total``.

    Each returned line is::

        {
            "product_id": …,
            "variant_id": …,
            "qty": …,
            "product": {…},
            "variant": {…},
            "line_total": round(variant["price"] * qty, 2),
        }

    Unknown ids raise ``KeyError`` (via the catalog lookups) so a broken line is
    never rendered silently.
    """
    lines = []
    for line in session.get(_CART_KEY, []):
        product = get_product(line["product_id"])
        variant = get_variant(line["product_id"], line["variant_id"])
        qty = line["qty"]
        lines.append(
            {
                "product_id": line["product_id"],
                "variant_id": line["variant_id"],
                "qty": qty,
                "product": product,
                "variant": variant,
                "line_total": round(variant["price"] * qty, 2),
            }
        )
    return lines


def cart_total(session):
    """Return the grand total of all cart lines (a float, ``0.0`` when empty)."""
    return float(round(sum(line["line_total"] for line in cart_lines(session)), 2))


def cart_count(session):
    """Return the total number of units in the cart (for the nav badge)."""
    return sum(line["qty"] for line in session.get(_CART_KEY, []))
