"""Tests for the real, session-backed cart (M5 -- real).

The cart lives in the Flask session under the key ``"cart"`` as an
order-preserving list of lines::

    [{"product_id": …, "variant_id": …, "qty": …}, …]

These tests exercise the real behavior of every helper in ``stal/cart.py``:
adding new lines, merging duplicates (capped at ``MAX_QTY``), updating and
removing lines, clearing the cart, enriching lines with catalog data and
``line_total``, computing the grand total and the unit count — plus the
quantity/product/variant validation edge cases. A short end-to-end section
uses the Flask test client to prove the real cart is actually wired into
``POST /oferta/dodaj`` and the shared nav badge, not just dead code.
"""

import pytest

from stal import cart
from stal.cart import (
    MAX_QTY,
    add_item,
    cart_count,
    cart_lines,
    cart_total,
    clear_cart,
    get_cart,
    remove_item,
    update_item,
)
from stal.catalog import get_product, get_variant

# Known-good catalog ids used throughout the suite.
PRODUCT = "sruby-m8x30"
VARIANT = "ocynkowana"
OTHER_VARIANT = "nierdzewna-a2"
SECOND_PRODUCT = "katownik-40x40x4"
SECOND_VARIANT = "3m-s235jr"

# Prices for the ids above (from the real catalog).
PRICE = 24.90
SECOND_PRICE = 62.00


def _line(product_id=PRODUCT, variant_id=VARIANT, qty=1):
    """Build a raw cart line dict."""
    return {"product_id": product_id, "variant_id": variant_id, "qty": qty}


# --- module-level API ------------------------------------------------------


def test_module_exposes_the_documented_api():
    for name in (
        "get_cart",
        "add_item",
        "update_item",
        "remove_item",
        "clear_cart",
        "cart_lines",
        "cart_total",
        "cart_count",
    ):
        assert callable(getattr(cart, name)), f"cart.{name} is not callable"


def test_max_qty_is_99():
    assert MAX_QTY == 99


# --- get_cart --------------------------------------------------------------


def test_get_cart_empty_session_returns_an_empty_list():
    assert get_cart({}) == []


def test_get_cart_returns_lines_for_a_populated_session():
    session = {"cart": [_line(qty=2)]}
    assert get_cart(session) == [_line(qty=2)]


def test_get_cart_returns_fresh_copies():
    """Mutating the returned list/dicts must not leak back into the session."""
    session = {"cart": [_line(qty=2)]}
    lines = get_cart(session)
    lines[0]["qty"] = 999
    lines.append(_line(product_id=SECOND_PRODUCT, variant_id=SECOND_VARIANT, qty=9))
    assert session["cart"] == [_line(qty=2)]


def test_get_cart_returns_a_fresh_list_each_call():
    session = {"cart": [_line(qty=1)]}
    first = get_cart(session)
    second = get_cart(session)
    assert first == second
    assert first is not second


# --- add_item: successful adds --------------------------------------------


def test_add_item_appends_a_new_line_and_returns_none():
    session = {}
    assert add_item(session, PRODUCT, VARIANT, 2) is None
    assert session["cart"] == [_line(qty=2)]


def test_add_item_merges_duplicate_product_and_variant():
    session = {"cart": [_line(qty=2)]}
    add_item(session, PRODUCT, VARIANT, 3)
    assert session["cart"] == [_line(qty=5)]


def test_add_item_keeps_distinct_lines_and_preserves_order():
    session = {"cart": [_line(qty=1)]}
    add_item(session, SECOND_PRODUCT, SECOND_VARIANT, 1)
    add_item(session, PRODUCT, OTHER_VARIANT, 4)
    assert session["cart"] == [
        _line(qty=1),
        _line(product_id=SECOND_PRODUCT, variant_id=SECOND_VARIANT, qty=1),
        _line(variant_id=OTHER_VARIANT, qty=4),
    ]


def test_add_item_allows_exactly_max_qty():
    session = {}
    add_item(session, PRODUCT, VARIANT, MAX_QTY)
    assert session["cart"] == [_line(qty=MAX_QTY)]


def test_add_item_merge_is_capped_at_max_qty():
    session = {"cart": [_line(qty=MAX_QTY - 9)]}
    add_item(session, PRODUCT, VARIANT, 20)
    assert session["cart"] == [_line(qty=MAX_QTY)]


def test_add_item_merge_does_not_exceed_max_when_already_full():
    session = {"cart": [_line(qty=MAX_QTY)]}
    add_item(session, PRODUCT, VARIANT, 5)
    assert session["cart"] == [_line(qty=MAX_QTY)]


# --- add_item: quantity validation ----------------------------------------


@pytest.mark.parametrize("qty", [0, -1, MAX_QTY + 1])
def test_add_item_rejects_out_of_range_quantity(qty):
    session = {}
    with pytest.raises(ValueError):
        add_item(session, PRODUCT, VARIANT, qty)
    assert session == {}


@pytest.mark.parametrize("qty", ["2", 2.0, None, True, False])
def test_add_item_rejects_non_integer_quantity(qty):
    session = {}
    with pytest.raises(ValueError):
        add_item(session, PRODUCT, VARIANT, qty)
    assert session == {}


def test_add_item_leaves_session_untouched_on_quantity_error():
    session = {"cart": [_line(qty=7)]}
    with pytest.raises(ValueError):
        add_item(session, PRODUCT, VARIANT, "abc")
    assert session == {"cart": [_line(qty=7)]}


# --- add_item: product/variant validation ---------------------------------


def test_add_item_rejects_unknown_product():
    session = {}
    with pytest.raises(KeyError):
        add_item(session, "nie-istnieje", VARIANT, 1)
    assert session == {}


def test_add_item_rejects_unknown_variant_for_known_product():
    session = {}
    with pytest.raises(KeyError):
        add_item(session, PRODUCT, "nie-istnieje", 1)
    assert session == {}


def test_add_item_leaves_session_untouched_on_unknown_ids():
    session = {"cart": [_line(qty=3)]}
    with pytest.raises(KeyError):
        add_item(session, "nie-istnieje", VARIANT, 1)
    assert session == {"cart": [_line(qty=3)]}


# --- update_item -----------------------------------------------------------


def test_update_item_sets_the_quantity_and_returns_none():
    session = {"cart": [_line(qty=1)]}
    assert update_item(session, PRODUCT, VARIANT, 5) is None
    assert session["cart"] == [_line(qty=5)]


@pytest.mark.parametrize("qty", [0, -1])
def test_update_item_removes_the_line_for_nonpositive_quantity(qty):
    session = {"cart": [_line(qty=3)]}
    update_item(session, PRODUCT, VARIANT, qty)
    assert session["cart"] == []


def test_update_item_allows_exactly_max_qty():
    session = {"cart": [_line(qty=1)]}
    update_item(session, PRODUCT, VARIANT, MAX_QTY)
    assert session["cart"] == [_line(qty=MAX_QTY)]


def test_update_item_rejects_quantity_above_max():
    session = {"cart": [_line(qty=1)]}
    with pytest.raises(ValueError):
        update_item(session, PRODUCT, VARIANT, MAX_QTY + 1)
    assert session["cart"] == [_line(qty=1)]


@pytest.mark.parametrize("qty", ["3", 3.0, None, True])
def test_update_item_rejects_non_integer_quantity(qty):
    session = {"cart": [_line(qty=1)]}
    with pytest.raises(ValueError):
        update_item(session, PRODUCT, VARIANT, qty)
    assert session["cart"] == [_line(qty=1)]


def test_update_item_missing_line_is_a_noop():
    session = {"cart": [_line(qty=2)]}
    assert update_item(session, SECOND_PRODUCT, SECOND_VARIANT, 9) is None
    assert session == {"cart": [_line(qty=2)]}


def test_update_item_empty_session_is_a_noop_without_creating_a_key():
    session = {}
    update_item(session, PRODUCT, VARIANT, 9)
    assert session == {}


# --- remove_item -----------------------------------------------------------


def test_remove_item_removes_only_the_matching_line():
    session = {
        "cart": [
            _line(qty=2),
            _line(product_id=SECOND_PRODUCT, variant_id=SECOND_VARIANT, qty=1),
        ]
    }
    assert remove_item(session, PRODUCT, VARIANT) is None
    assert session["cart"] == [
        _line(product_id=SECOND_PRODUCT, variant_id=SECOND_VARIANT, qty=1)
    ]


def test_remove_item_missing_line_is_a_noop():
    session = {"cart": [_line(qty=2)]}
    remove_item(session, PRODUCT, OTHER_VARIANT)
    assert session == {"cart": [_line(qty=2)]}


def test_remove_item_empty_session_is_a_noop_without_creating_a_key():
    session = {}
    remove_item(session, PRODUCT, VARIANT)
    assert session == {}


# --- clear_cart ------------------------------------------------------------


def test_clear_cart_empties_the_cart_and_returns_none():
    session = {"cart": [_line(qty=2), _line(product_id=SECOND_PRODUCT, variant_id=SECOND_VARIANT, qty=1)]}
    assert clear_cart(session) is None
    assert session["cart"] == []


def test_clear_cart_on_an_empty_session_still_creates_the_cart_key():
    session = {}
    clear_cart(session)
    assert session == {"cart": []}


# --- cart_lines ------------------------------------------------------------


def test_cart_lines_empty_session_returns_an_empty_list():
    assert cart_lines({}) == []


def test_cart_lines_enriches_with_product_variant_and_line_total():
    session = {"cart": [_line(qty=2)]}
    lines = cart_lines(session)
    assert len(lines) == 1
    line = lines[0]
    assert line["product"] == get_product(PRODUCT)
    assert line["variant"] == get_variant(PRODUCT, VARIANT)
    assert line["product_id"] == PRODUCT
    assert line["variant_id"] == VARIANT
    assert line["qty"] == 2
    assert line["line_total"] == round(PRICE * 2, 2)


def test_cart_lines_computes_each_line_total():
    session = {
        "cart": [
            _line(qty=3),
            _line(product_id=SECOND_PRODUCT, variant_id=SECOND_VARIANT, qty=1),
        ]
    }
    totals = [line["line_total"] for line in cart_lines(session)]
    assert totals == [round(PRICE * 3, 2), round(SECOND_PRICE * 1, 2)]


def test_cart_lines_returns_fresh_enriched_lines():
    session = {"cart": [_line(qty=1)]}
    first = cart_lines(session)
    second = cart_lines(session)
    assert first == second
    assert first is not second
    assert first[0] is not second[0]


def test_cart_lines_rejects_unknown_product():
    with pytest.raises(KeyError):
        cart_lines({"cart": [_line(product_id="nie-istnieje")]})


def test_cart_lines_rejects_unknown_variant():
    with pytest.raises(KeyError):
        cart_lines({"cart": [_line(variant_id="nie-istnieje")]})


# --- cart_total ------------------------------------------------------------


def test_cart_total_empty_session_is_zero_float():
    total = cart_total({})
    assert total == 0.0
    assert isinstance(total, float)


def test_cart_total_sums_all_line_totals():
    session = {
        "cart": [
            _line(qty=2),
            _line(product_id=SECOND_PRODUCT, variant_id=SECOND_VARIANT, qty=1),
        ]
    }
    assert cart_total(session) == pytest.approx(round(PRICE * 2, 2) + SECOND_PRICE)


# --- cart_count ------------------------------------------------------------


def test_cart_count_empty_session_is_zero():
    assert cart_count({}) == 0
    assert isinstance(cart_count({}), int)


def test_cart_count_sums_units_across_lines():
    session = {
        "cart": [
            _line(qty=2),
            _line(product_id=SECOND_PRODUCT, variant_id=SECOND_VARIANT, qty=5),
        ]
    }
    assert cart_count(session) == 7
    assert isinstance(cart_count(session), int)


# --- end-to-end wiring through the app -------------------------------------


def test_add_to_cart_route_persists_the_line_in_the_signed_session(client):
    resp = client.post(
        "/oferta/dodaj",
        data={"product_id": PRODUCT, "variant_id": VARIANT, "qty": "2"},
    )
    assert resp.status_code == 302

    with client.session_transaction() as sess:
        assert sess["cart"] == [_line(qty=2)]


def test_add_to_cart_route_merges_duplicates_in_the_session(client):
    client.post(
        "/oferta/dodaj",
        data={"product_id": PRODUCT, "variant_id": VARIANT, "qty": "2"},
    )
    client.post(
        "/oferta/dodaj",
        data={"product_id": PRODUCT, "variant_id": VARIANT, "qty": "3"},
    )
    with client.session_transaction() as sess:
        assert sess["cart"] == [_line(qty=5)]


def test_add_to_cart_route_updates_the_nav_badge_with_real_quantity(client):
    client.post(
        "/oferta/dodaj",
        data={"product_id": PRODUCT, "variant_id": VARIANT, "qty": "2"},
    )
    client.post(
        "/oferta/dodaj",
        data={"product_id": SECOND_PRODUCT, "variant_id": SECOND_VARIANT, "qty": "1"},
    )
    html = client.get("/oferta").get_data(as_text=True)
    assert '<span class="cart-count">3</span>' in html
