"""Tests for M5 (stub): cart helpers returning fixed/empty data.

These validate the current stub deliverable only:
- `stal/cart.py` exists and exposes the full documented cart API
  (`get_cart`, `add_item`, `update_item`, `remove_item`, `clear_cart`,
  `cart_lines`, `cart_total`, `cart_count`),
- every helper accepts a `session` argument (a dict or `None`) without error,
- the readers return the documented fixed/empty values (`[]`, `0.0`, `0`),
- the mutators are true no-ops: they return `None` and never touch the
  `session` object passed in (no real session logic in the stub pass),
- the returned empty containers are fresh objects, not shared singletons.

The real, session-backed implementation (validation, line merging, totals)
arrives in the real pass and is tested in `tests/test_cart.py` (currently a stub smoke test).
"""

from stal import cart
from stal.cart import (
    add_item,
    cart_count,
    cart_lines,
    cart_total,
    clear_cart,
    get_cart,
    remove_item,
    update_item,
)

# A populated session: the stub must ignore it entirely.
POPULATED_SESSION = {
    "cart": [
        {"product_id": "sruby-m8x30", "variant_id": "ocynkowana", "qty": 4},
    ]
}

READERS = [get_cart, cart_lines, cart_total, cart_count]
# Each mutator maps to the trailing args it expects after `session`.
MUTATORS = [
    (add_item, ("sruby-m8x30", "ocynkowana", 2)),
    (update_item, ("sruby-m8x30", "ocynkowana", 5)),
    (remove_item, ("sruby-m8x30", "ocynkowana")),
    (clear_cart, ()),
]


# --- module-level API ------------------------------------------------------


def test_cart_module_exposes_the_public_api():
    assert cart.get_cart is get_cart
    assert cart.add_item is add_item
    assert cart.update_item is update_item
    assert cart.remove_item is remove_item
    assert cart.clear_cart is clear_cart
    assert cart.cart_lines is cart_lines
    assert cart.cart_total is cart_total
    assert cart.cart_count is cart_count


def test_every_helper_accepts_a_session_argument():
    """All helpers take `session` first and never raise on a dict or `None`."""
    for helper in READERS:
        helper(POPULATED_SESSION)
        helper(None)
    for helper, args in MUTATORS:
        helper(POPULATED_SESSION, *args)
        helper(None, *args)


# --- readers return fixed/empty data ---------------------------------------


def test_get_cart_returns_an_empty_list():
    result = get_cart(POPULATED_SESSION)
    assert isinstance(result, list)
    assert result == []


def test_get_cart_ignores_existing_session_cart():
    """Even a session with cart lines yields an empty cart in the stub."""
    assert get_cart(POPULATED_SESSION) == []
    assert get_cart({"cart": [{"product_id": "x", "variant_id": "y", "qty": 1}]}) == []


def test_cart_lines_returns_an_empty_list():
    result = cart_lines(POPULATED_SESSION)
    assert isinstance(result, list)
    assert result == []


def test_cart_total_returns_zero_as_a_float():
    result = cart_total(POPULATED_SESSION)
    assert isinstance(result, float)
    assert result == 0.0


def test_cart_count_returns_zero_as_an_int():
    result = cart_count(POPULATED_SESSION)
    assert isinstance(result, int)
    assert result == 0


# --- mutators are no-ops returning None ------------------------------------


def test_add_item_is_a_noop_that_returns_none():
    assert add_item(POPULATED_SESSION, "sruby-m8x30", "ocynkowana", 3) is None


def test_update_item_is_a_noop_that_returns_none():
    assert update_item(POPULATED_SESSION, "sruby-m8x30", "ocynkowana", 9) is None


def test_remove_item_is_a_noop_that_returns_none():
    assert remove_item(POPULATED_SESSION, "sruby-m8x30", "ocynkowana") is None


def test_clear_cart_is_a_noop_that_returns_none():
    assert clear_cart(POPULATED_SESSION) is None


def test_mutating_helpers_leave_the_session_dict_untouched():
    """The stub has no real session logic: the passed dict must be unchanged."""
    session = dict(POPULATED_SESSION)
    before = repr(session)

    add_item(session, "sruby-m8x30", "ocynkowana", 1)
    update_item(session, "sruby-m8x30", "ocynkowana", 1)
    remove_item(session, "sruby-m8x30", "ocynkowana")
    clear_cart(session)

    assert repr(session) == before
    assert session["cart"] == POPULATED_SESSION["cart"]


def test_helpers_return_fresh_containers_not_shared_singletons():
    """Mutating one returned container must not leak into the next call."""
    first = get_cart(None)
    second = get_cart(None)
    assert first == second == []
    assert first is not second

    lines_first = cart_lines(None)
    lines_second = cart_lines(None)
    assert lines_first == lines_second == []
    assert lines_first is not lines_second
