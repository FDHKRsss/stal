"""Tests for M7 (real): mocked order confirmation.

These validate the real deliverable only:
- `stal/templates/confirmation.html` exists, extends `base.html` and renders the
  order number, the item table, the total and the chosen payment/delivery,
- GET `/zamowienie` redirects to `/koszyk` (nothing to submit via GET),
- POST `/zamowienie` validates a non-empty cart, a known payment method, a known
  delivery location and (for deliveries) an address, then renders the mocked
  confirmation with a `ZAM-YYYYMMDD-HHMMSS` order number, the live items/total
  and the chosen payment/delivery, and finally clears the cart,
- invalid input never crashes: it flashes a Polish message and redirects back,
- the confirmation is clearly marked as a demo („wersja demonstracyjna").
"""

import re
from pathlib import Path

from stal.cart import add_item, cart_count
from stal.catalog import get_product, get_variant

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "stal" / "templates"

ORDER = "/zamowienie"
CART = "/koszyk"
OFFER = "/oferta"

# Two known catalog lines used to seed a non-empty cart for the success path.
P1 = get_product("sruby-m8x30")
V1 = get_variant("sruby-m8x30", "ocynkowana")
P2 = get_product("katownik-40x40x4")
V2 = get_variant("katownik-40x40x4", "6m-s235jr")

QTY1 = 2
QTY2 = 1
TOTAL = round(V1["price"] * QTY1 + V2["price"] * QTY2, 2)

PICKUP = "odbior"


def _price(value):
    """Mirror the app's ``format_price`` filter (``24,90 zł``)."""
    return f"{value:.2f}".replace(".", ",") + " zł"


def _seed_cart(client):
    """Add the two known lines into the signed session cart."""
    with client.session_transaction() as sess:
        add_item(sess, P1["id"], V1["id"], QTY1)
        add_item(sess, P2["id"], V2["id"], QTY2)


def _valid_payload(**overrides):
    data = {
        "payment_method": "przelew",
        "delivery_method": "kurier",
        "address": "ul. Stalowa 1, 00-001 Warszawa",
    }
    data.update(overrides)
    return data


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


def test_confirmation_template_file_exists():
    assert (TEMPLATES / "confirmation.html").is_file()


def test_confirmation_template_extends_base_and_fills_blocks():
    tpl = (TEMPLATES / "confirmation.html").read_text(encoding="utf-8")
    assert '{% extends "base.html" %}' in tpl
    assert "{% block title %}" in tpl
    assert "{% block content %}" in tpl


def test_confirmation_template_has_the_acceptance_heading():
    tpl = (TEMPLATES / "confirmation.html").read_text(encoding="utf-8")
    assert "<h1>Zamówienie przyjęte</h1>" in tpl


def test_confirmation_template_renders_a_dynamic_order_number():
    tpl = (TEMPLATES / "confirmation.html").read_text(encoding="utf-8")
    assert "{{ order.number }}" in tpl


def test_confirmation_template_renders_the_item_table():
    tpl = (TEMPLATES / "confirmation.html").read_text(encoding="utf-8")
    assert "{% for line in lines %}" in tpl
    assert "{{ line.product.name }}" in tpl
    assert "{{ line.variant.label }}" in tpl
    assert "{{ line.qty }}" in tpl
    assert "{{ line.line_total | format_price }}" in tpl


def test_confirmation_template_renders_the_total():
    tpl = (TEMPLATES / "confirmation.html").read_text(encoding="utf-8")
    assert "{{ total | format_price }}" in tpl


def test_confirmation_template_renders_payment_delivery_and_address():
    tpl = (TEMPLATES / "confirmation.html").read_text(encoding="utf-8")
    assert "{{ order.payment_label }}" in tpl
    assert "{{ order.delivery_label }}" in tpl
    assert "{{ order.address }}" in tpl


def test_confirmation_template_marks_the_page_as_a_demo():
    tpl = (TEMPLATES / "confirmation.html").read_text(encoding="utf-8")
    assert "wersja demonstracyjna" in tpl.lower()


def test_confirmation_template_links_back_to_the_homepage():
    tpl = (TEMPLATES / "confirmation.html").read_text(encoding="utf-8")
    assert "url_for('index')" in tpl


# --- GET /zamowienie -------------------------------------------------------


def test_get_order_redirects_to_the_cart(client):
    resp = client.get(ORDER)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(CART)


def test_get_order_redirect_lands_on_the_cart_page(client):
    """Following the GET redirect reaches the summary, not the confirmation."""
    resp = client.get(ORDER, follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "<h1>Koszyk</h1>" in html
    assert "<h1>Zamówienie przyjęte</h1>" not in html


# --- POST /zamowienie: validation ------------------------------------------


def test_empty_cart_is_rejected_without_crashing(client):
    resp = client.post(ORDER, data=_valid_payload(), follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Twój koszyk jest pusty." in html
    assert "flash flash-error" in html
    # It lands back on the summary, never on the confirmation.
    assert "<h1>Koszyk</h1>" in html
    assert "<h1>Zamówienie przyjęte</h1>" not in html


def test_unknown_payment_method_is_rejected_without_losing_the_cart(client):
    _seed_cart(client)
    resp = client.post(
        ORDER,
        data=_valid_payload(payment_method="nieznany"),
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Wybierz prawidłowy sposób płatności." in html
    assert "flash flash-error" in html
    with client.session_transaction() as sess:
        assert cart_count(sess) == QTY1 + QTY2


def test_unknown_delivery_method_is_rejected_without_losing_the_cart(client):
    _seed_cart(client)
    resp = client.post(
        ORDER,
        data=_valid_payload(delivery_method="nieznany"),
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Wybierz prawidłowe miejsce dostawy." in html
    assert "flash flash-error" in html
    with client.session_transaction() as sess:
        assert cart_count(sess) == QTY1 + QTY2


def test_delivery_without_address_is_rejected(client):
    _seed_cart(client)
    resp = client.post(
        ORDER,
        data=_valid_payload(delivery_method="kurier", address=""),
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Podaj adres dostawy" in html
    assert "flash flash-error" in html
    with client.session_transaction() as sess:
        assert cart_count(sess) == QTY1 + QTY2


def test_blank_address_is_treated_as_missing(client):
    _seed_cart(client)
    resp = client.post(
        ORDER,
        data=_valid_payload(delivery_method="kurier", address="   "),
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Podaj adres dostawy" in html


def test_invalid_input_never_crashes(client):
    """Any garbage payload yields a redirect, never a 500."""
    _seed_cart(client)
    resp = client.post(
        ORDER,
        data={"payment_method": "?", "delivery_method": "?", "address": "?"},
    )
    assert resp.status_code == 302


def test_broken_cart_line_is_cleared_and_redirects_to_the_offer(client):
    """A stale/tampered cart line (unknown catalog id) is dropped safely."""
    with client.session_transaction() as sess:
        sess["cart"] = [
            {"product_id": "nie-istnieje", "variant_id": "x", "qty": 1}
        ]
    resp = client.post(
        ORDER,
        data=_valid_payload(),
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Koszyk zawierał nieaktualne pozycje i został wyczyszczony." in html
    assert "flash flash-error" in html
    assert "<h1>Oferta</h1>" in html
    with client.session_transaction() as sess:
        assert cart_count(sess) == 0


# --- POST /zamowienie: success ---------------------------------------------


def test_place_order_renders_the_confirmation_with_live_items(client):
    _seed_cart(client)
    resp = client.post(ORDER, data=_valid_payload())
    assert resp.status_code == 200
    assert resp.mimetype == "text/html"
    html = resp.get_data(as_text=True)
    assert "<!doctype html>" in html
    assert '<html lang="pl">' in html
    assert "<h1>Zamówienie przyjęte</h1>" in html
    assert P1["name"] in html
    assert V1["label"] in html
    assert P2["name"] in html
    assert V2["label"] in html


def test_place_order_shows_the_line_totals_and_grand_total(client):
    _seed_cart(client)
    html = client.post(ORDER, data=_valid_payload()).get_data(as_text=True)
    assert _price(V1["price"] * QTY1) in html
    assert _price(V2["price"] * QTY2) in html
    assert f"Razem do zapłaty: {_price(TOTAL)}" in html


def test_place_order_generates_a_clock_based_mock_order_number(client):
    _seed_cart(client)
    html = client.post(ORDER, data=_valid_payload()).get_data(as_text=True)
    assert "Numer zamówienia:" in html
    assert re.search(r"ZAM-\d{8}-\d{6}", html) is not None
    assert "przykładowy" in html


def test_place_order_shows_the_chosen_payment_method(client):
    _seed_cart(client)
    html = client.post(
        ORDER, data=_valid_payload(payment_method="karta")
    ).get_data(as_text=True)
    assert "karta płatnicza online" in html


def test_place_order_shows_the_chosen_delivery_and_address(client):
    _seed_cart(client)
    html = client.post(
        ORDER,
        data=_valid_payload(
            delivery_method="transport", address="ul. Hutnicza 9, 30-001 Kraków"
        ),
    ).get_data(as_text=True)
    assert "dostawa transportem własnym" in html
    assert "ul. Hutnicza 9, 30-001 Kraków" in html


def test_pickup_does_not_require_an_address_and_ignores_a_submitted_one(client):
    _seed_cart(client)
    html = client.post(
        ORDER,
        data=_valid_payload(delivery_method=PICKUP, address="ignorowany adres"),
    ).get_data(as_text=True)
    assert "odbiór osobisty (magazyn)" in html
    assert "ignorowany adres" not in html


def test_place_order_clears_the_cart_after_success(client):
    _seed_cart(client)
    resp = client.post(ORDER, data=_valid_payload())
    assert resp.status_code == 200
    with client.session_transaction() as sess:
        assert cart_count(sess) == 0


def test_place_order_is_clearly_marked_as_a_demo(client):
    _seed_cart(client)
    html = client.post(ORDER, data=_valid_payload()).get_data(as_text=True).lower()
    assert "wersja demonstracyjna" in html
    assert "demonstracyjna" in html
    assert "stub" not in html


# --- cart page checkout form -----------------------------------------------


def test_cart_page_checkout_form_posts_to_the_order_route(client):
    html = client.get(CART).get_data(as_text=True)
    assert f'action="{ORDER}"' in html
    assert "Złóż zamówienie" in html


def test_checkout_form_submits_payment_delivery_and_address(client):
    html = client.get(CART).get_data(as_text=True)
    form = _checkout_form(html)
    assert 'name="payment_method"' in form
    assert 'name="delivery_method"' in form
    assert 'name="address"' in form
