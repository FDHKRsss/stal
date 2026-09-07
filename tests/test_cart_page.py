"""Tests for M6 (real): summary / checkout page.

These validate the real deliverable only:
- `stal/templates/cart.html` exists, extends `base.html` and renders the live
  session-backed cart lines (product name, variant label, editable quantity and
  line total) plus the grand total,
- an empty cart shows "Koszyk jest pusty." and a `0,00 zł` total,
- every line has a per-line **Aktualizuj** form and a per-line **Usuń** form
  posting to `/koszyk/aktualizuj`,
- the mocked payment-method radios and delivery `<select>` (plus the address
  field) still render, and the checkout form still posts to `/zamowienie`,
- POST `/koszyk/aktualizuj` updates a line's quantity or removes that line and
  flashes a Polish success/error message; invalid quantity input never crashes
  and never mutates the cart,
- a broken (stale/tampered) cart line is dropped instead of crashing,
- GET `/koszyk/aktualizuj` (and POST `/koszyk`) are rejected with 405.

The stub for this milestone lived in `tests/test_cart_page_stub.py`, which is
replaced by this file.
"""

import re
from pathlib import Path

import pytest

from stal.cart import MAX_QTY, add_item, cart_count
from stal.catalog import get_product, get_variant

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "stal" / "templates"

CART = "/koszyk"
UPDATE = "/koszyk/aktualizuj"
OFFER = "/oferta"

PAYMENT_VALUES = ("przelew", "karta", "gotowka", "odroczony")
DELIVERY_VALUES = ("odbior", "kurier", "transport")

# Two known catalog lines used to seed a non-empty cart for the success path.
P1 = get_product("sruby-m8x30")
V1 = get_variant("sruby-m8x30", "ocynkowana")
P2 = get_product("katownik-40x40x4")
V2 = get_variant("katownik-40x40x4", "6m-s235jr")

QTY1 = 2
QTY2 = 1
TOTAL = round(V1["price"] * QTY1 + V2["price"] * QTY2, 2)


def _price(value):
    """Mirror the app's ``format_price`` filter (``24,90 zł``)."""
    return f"{value:.2f}".replace(".", ",") + " zł"


def _seed_cart(client):
    """Add the two known lines into the signed session cart."""
    with client.session_transaction() as sess:
        add_item(sess, P1["id"], V1["id"], QTY1)
        add_item(sess, P2["id"], V2["id"], QTY2)


def _line_for(sess, product_id, variant_id):
    return next(
        line
        for line in sess["cart"]
        if line["product_id"] == product_id and line["variant_id"] == variant_id
    )


def _checkout_form(html):
    """Extract the ``/zamowienie`` checkout form block from the cart page."""
    match = re.search(
        r'<form[^>]*action="[^"]*zamowienie[^"]*"[^>]*>(.*?)</form>',
        html,
        re.DOTALL,
    )
    assert match, "checkout form posting to /zamowienie not found"
    return match.group(0)


# --- template files -------------------------------------------------------


def test_cart_template_file_exists():
    assert (TEMPLATES / "cart.html").is_file()


def test_cart_template_extends_base_and_fills_blocks():
    cart = (TEMPLATES / "cart.html").read_text(encoding="utf-8")
    assert '{% extends "base.html" %}' in cart
    assert "{% block title %}" in cart
    assert "{% block content %}" in cart


def test_cart_template_has_per_line_update_and_remove_forms():
    cart = (TEMPLATES / "cart.html").read_text(encoding="utf-8")
    assert 'class="line-update-form"' in cart
    assert 'class="line-remove-form"' in cart
    assert "url_for('update_cart')" in cart
    assert 'name="action"' in cart
    assert 'value="update"' in cart
    assert 'value="remove"' in cart
    assert 'name="product_id"' in cart
    assert 'name="variant_id"' in cart
    assert 'name="qty"' in cart
    assert "Aktualizuj" in cart
    assert "Usuń" in cart


def test_cart_template_has_checkout_form_posting_to_order_route():
    cart = (TEMPLATES / "cart.html").read_text(encoding="utf-8")
    assert "url_for('place_order')" in cart
    assert 'method="post"' in cart
    assert 'name="payment_method"' in cart
    assert 'name="delivery_method"' in cart
    assert 'name="address"' in cart


def test_cart_template_renders_payment_and_delivery_from_the_route_dicts():
    cart = (TEMPLATES / "cart.html").read_text(encoding="utf-8")
    assert "payment_methods.items()" in cart
    assert "delivery_methods.items()" in cart


def test_cart_template_links_back_to_the_offer():
    cart = (TEMPLATES / "cart.html").read_text(encoding="utf-8")
    assert "url_for('offer')" in cart


# --- GET /koszyk (empty cart) --------------------------------------------


def test_cart_route_returns_html(client):
    resp = client.get(CART)
    assert resp.status_code == 200
    assert resp.mimetype == "text/html"


def test_cart_route_renders_the_cart_template(client):
    html = client.get(CART).get_data(as_text=True)
    assert "<!doctype html>" in html
    assert '<html lang="pl">' in html
    assert "<h1>Koszyk</h1>" in html


def test_cart_page_has_the_real_title_without_stub_marker(client):
    html = client.get(CART).get_data(as_text=True)
    assert "<title>Stal — koszyk</title>" in html
    assert "(stub)" not in html


def test_empty_cart_shows_empty_note_and_zero_total(client):
    html = client.get(CART).get_data(as_text=True)
    assert "Koszyk jest pusty." in html
    assert "Razem do zapłaty: 0,00 zł" in html


def test_cart_page_shows_mocked_payment_methods(client):
    html = client.get(CART).get_data(as_text=True)
    for value in PAYMENT_VALUES:
        assert f'name="payment_method" value="{value}"' in html
    # The first option is pre-selected so the demo always has a value.
    assert 'name="payment_method" value="przelew" checked' in html


def test_cart_page_shows_mocked_delivery_options(client):
    html = client.get(CART).get_data(as_text=True)
    for value in DELIVERY_VALUES:
        assert f'<option value="{value}">' in html


def test_cart_page_shows_an_address_field(client):
    html = client.get(CART).get_data(as_text=True)
    assert 'name="address"' in html
    assert "Adres dostawy" in html
    assert "Wymagany, jeśli nie wybierasz odbioru osobistego." in html


def test_cart_page_is_clearly_marked_as_a_demo(client):
    html = client.get(CART).get_data(as_text=True).lower()
    assert "wersja demonstracyjna" in html
    assert "stub" not in html


# --- GET /koszyk (populated cart) ----------------------------------------


def test_cart_page_renders_live_cart_lines_and_totals(client):
    _seed_cart(client)
    html = client.get(CART).get_data(as_text=True)
    assert P1["name"] in html
    assert V1["label"] in html
    assert P2["name"] in html
    assert V2["label"] in html
    assert _price(V1["price"] * QTY1) in html
    assert _price(V2["price"] * QTY2) in html
    assert f"Razem do zapłaty: {_price(TOTAL)}" in html
    assert "Koszyk jest pusty." not in html


def test_cart_page_renders_one_update_and_remove_form_per_line(client):
    _seed_cart(client)
    html = client.get(CART).get_data(as_text=True)
    assert html.count('<form class="line-update-form"') == 2
    assert html.count('<form class="line-remove-form"') == 2


def test_cart_page_renders_editable_quantity_inputs(client):
    _seed_cart(client)
    html = client.get(CART).get_data(as_text=True)
    assert '<input type="number" name="qty" value="2" min="1" max="99">' in html
    assert '<input type="number" name="qty" value="1" min="1" max="99">' in html


# --- POST /koszyk/aktualizuj (update) -------------------------------------


def test_update_route_redirects_back_to_the_cart(client):
    _seed_cart(client)
    resp = client.post(
        UPDATE,
        data={
            "action": "update",
            "product_id": P1["id"],
            "variant_id": V1["id"],
            "qty": "5",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(CART)


def test_update_route_updates_the_matching_line_only(client):
    _seed_cart(client)
    client.post(
        UPDATE,
        data={
            "action": "update",
            "product_id": P1["id"],
            "variant_id": V1["id"],
            "qty": "5",
        },
    )
    with client.session_transaction() as sess:
        assert _line_for(sess, P1["id"], V1["id"])["qty"] == 5
        assert _line_for(sess, P2["id"], V2["id"])["qty"] == QTY2


def test_update_route_allows_exactly_max_qty(client):
    _seed_cart(client)
    client.post(
        UPDATE,
        data={
            "action": "update",
            "product_id": P1["id"],
            "variant_id": V1["id"],
            "qty": str(MAX_QTY),
        },
    )
    with client.session_transaction() as sess:
        assert _line_for(sess, P1["id"], V1["id"])["qty"] == MAX_QTY


def test_update_route_flashes_a_polish_success_message(client):
    _seed_cart(client)
    resp = client.post(
        UPDATE,
        data={
            "action": "update",
            "product_id": P1["id"],
            "variant_id": V1["id"],
            "qty": "5",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Zaktualizowano koszyk." in html
    assert "flash flash-success" in html


def test_missing_action_defaults_to_update(client):
    _seed_cart(client)
    client.post(
        UPDATE,
        data={"product_id": P1["id"], "variant_id": V1["id"], "qty": "7"},
    )
    with client.session_transaction() as sess:
        assert _line_for(sess, P1["id"], V1["id"])["qty"] == 7


# --- POST /koszyk/aktualizuj (validation) ---------------------------------


def test_non_integer_quantity_is_rejected_without_mutating_the_cart(client):
    _seed_cart(client)
    resp = client.post(
        UPDATE,
        data={
            "action": "update",
            "product_id": P1["id"],
            "variant_id": V1["id"],
            "qty": "abc",
        },
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Ilość musi być liczbą całkowitą." in html
    assert "flash flash-error" in html
    with client.session_transaction() as sess:
        assert _line_for(sess, P1["id"], V1["id"])["qty"] == QTY1


@pytest.mark.parametrize("qty", ["0", "-5", str(MAX_QTY + 1)])
def test_out_of_range_quantity_is_rejected_without_mutating_the_cart(client, qty):
    _seed_cart(client)
    resp = client.post(
        UPDATE,
        data={
            "action": "update",
            "product_id": P1["id"],
            "variant_id": V1["id"],
            "qty": qty,
        },
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert f"Ilość musi być liczbą od 1 do {MAX_QTY}." in html
    assert "flash flash-error" in html
    with client.session_transaction() as sess:
        assert _line_for(sess, P1["id"], V1["id"])["qty"] == QTY1


def test_invalid_update_still_redirects_back_to_the_cart(client):
    _seed_cart(client)
    resp = client.post(UPDATE, data={"action": "update", "qty": "abc"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(CART)


# --- POST /koszyk/aktualizuj (remove) -------------------------------------


def test_remove_route_redirects_back_to_the_cart(client):
    _seed_cart(client)
    resp = client.post(
        UPDATE,
        data={
            "action": "remove",
            "product_id": P1["id"],
            "variant_id": V1["id"],
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(CART)


def test_remove_route_removes_only_the_matching_line(client):
    _seed_cart(client)
    client.post(
        UPDATE,
        data={
            "action": "remove",
            "product_id": P1["id"],
            "variant_id": V1["id"],
        },
    )
    with client.session_transaction() as sess:
        assert len(sess["cart"]) == 1
        assert sess["cart"][0]["product_id"] == P2["id"]
        assert sess["cart"][0]["variant_id"] == V2["id"]
        assert sess["cart"][0]["qty"] == QTY2


def test_remove_route_flashes_a_polish_success_message(client):
    _seed_cart(client)
    resp = client.post(
        UPDATE,
        data={
            "action": "remove",
            "product_id": P1["id"],
            "variant_id": V1["id"],
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Usunięto pozycję z koszyka." in html
    assert "flash flash-success" in html


# --- broken / tampered cart line -----------------------------------------


def test_broken_cart_line_redirects_to_the_offer(client):
    with client.session_transaction() as sess:
        sess["cart"] = [
            {"product_id": "nie-istnieje", "variant_id": "x", "qty": 1}
        ]
    resp = client.get(CART)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(OFFER)


def test_broken_cart_line_is_cleared_with_a_polish_error(client):
    with client.session_transaction() as sess:
        sess["cart"] = [
            {"product_id": "nie-istnieje", "variant_id": "x", "qty": 1}
        ]
    resp = client.get(CART, follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Koszyk zawierał nieaktualne pozycje i został wyczyszczony." in html
    assert "flash flash-error" in html
    assert "<h1>Oferta</h1>" in html
    with client.session_transaction() as sess:
        assert cart_count(sess) == 0


# --- checkout form integration (M7 preserved) -----------------------------


def test_cart_page_checkout_form_posts_to_the_order_route(client):
    html = client.get(CART).get_data(as_text=True)
    assert 'action="/zamowienie"' in html
    assert "Złóż zamówienie" in html


def test_checkout_form_submits_payment_delivery_and_address(client):
    html = client.get(CART).get_data(as_text=True)
    form = _checkout_form(html)
    assert 'name="payment_method"' in form
    assert 'name="delivery_method"' in form
    assert 'name="address"' in form


# --- method handling ------------------------------------------------------


def test_update_route_rejects_get(client):
    resp = client.get(UPDATE)
    assert resp.status_code == 405


def test_cart_route_rejects_post(client):
    resp = client.post(CART)
    assert resp.status_code == 405
