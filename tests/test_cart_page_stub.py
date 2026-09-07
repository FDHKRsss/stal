"""Tests for M6 (stub): summary / checkout page.

These validate the current stub deliverable only:
- `stal/templates/cart.html` exists and extends `base.html`,
- GET `/koszyk` renders it (HTML) as a static summary stub: an empty-cart
  note with a `0,00 zł` total, mocked payment-method radios, a mocked delivery
  `<select>` plus an address field, and a link back to the offer,
- the "Zaktualizuj koszyk" form posts to `/koszyk/aktualizuj`,
- POST `/koszyk/aktualizuj` flashes a fixed demo message and redirects back to
  `/koszyk` (the stub ignores the submitted form),
- the flash message is actually rendered and does not leak to a fresh GET,
- GET `/koszyk/aktualizuj` (and POST `/koszyk`) are rejected with 405.

The real summary page (rendering live cart lines, per-line update/remove forms
and conditional address validation) arrives in the real pass and is tested in
`tests/test_routes.py` (not yet written).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "stal" / "templates"

CART = "/koszyk"
UPDATE = "/koszyk/aktualizuj"
FLASH_TEXT = "Koszyk zaktualizowany (wersja demonstracyjna)."

PAYMENT_VALUES = ("przelew", "karta", "gotowka", "odroczony")
DELIVERY_VALUES = ("odbior", "kurier", "transport")


# --- template files -------------------------------------------------------


def test_cart_template_file_exists():
    assert (TEMPLATES / "cart.html").is_file()


def test_cart_template_extends_base_and_fills_content():
    cart = (TEMPLATES / "cart.html").read_text(encoding="utf-8")
    assert '{% extends "base.html" %}' in cart
    assert "{% block title %}" in cart
    assert "{% block content %}" in cart


def test_cart_template_posts_to_the_update_route():
    cart = (TEMPLATES / "cart.html").read_text(encoding="utf-8")
    assert "url_for('update_cart')" in cart
    assert 'method="post"' in cart


def test_cart_template_has_mocked_payment_radio_options():
    cart = (TEMPLATES / "cart.html").read_text(encoding="utf-8")
    assert 'name="payment_method"' in cart
    for value in PAYMENT_VALUES:
        assert f'value="{value}"' in cart


def test_cart_template_has_mocked_delivery_select_options():
    cart = (TEMPLATES / "cart.html").read_text(encoding="utf-8")
    assert 'name="delivery_method"' in cart
    for value in DELIVERY_VALUES:
        assert f'value="{value}"' in cart


def test_cart_template_has_an_address_field():
    cart = (TEMPLATES / "cart.html").read_text(encoding="utf-8")
    assert 'name="address"' in cart


def test_cart_template_links_back_to_the_offer():
    cart = (TEMPLATES / "cart.html").read_text(encoding="utf-8")
    assert "url_for('offer')" in cart


# --- GET /koszyk ----------------------------------------------------------


def test_cart_route_returns_html(client):
    resp = client.get(CART)
    assert resp.status_code == 200
    assert resp.mimetype == "text/html"


def test_cart_route_renders_the_cart_template(client):
    html = client.get(CART).get_data(as_text=True)
    assert "<!doctype html>" in html
    assert '<html lang="pl">' in html
    assert "<h1>Koszyk</h1>" in html


def test_cart_page_overrides_the_title_block(client):
    html = client.get(CART).get_data(as_text=True)
    assert "<title>Stal — koszyk (stub)</title>" in html


def test_cart_page_shows_an_empty_cart_note(client):
    html = client.get(CART).get_data(as_text=True)
    assert "Koszyk jest pusty" in html


def test_cart_page_shows_a_zero_total(client):
    html = client.get(CART).get_data(as_text=True)
    assert "0,00 zł" in html


def test_cart_page_shows_mocked_payment_methods(client):
    html = client.get(CART).get_data(as_text=True)
    for value in PAYMENT_VALUES:
        assert f'name="payment_method" value="{value}"' in html
    # One option is pre-selected so the demo always has a value.
    assert 'name="payment_method" value="przelew" checked' in html


def test_cart_page_shows_mocked_delivery_options(client):
    html = client.get(CART).get_data(as_text=True)
    for value in DELIVERY_VALUES:
        assert f'<option value="{value}">' in html


def test_cart_page_shows_an_address_field(client):
    html = client.get(CART).get_data(as_text=True)
    assert 'name="address"' in html
    assert "Adres dostawy" in html


def test_cart_page_has_an_update_form_posting_to_update_route(client):
    html = client.get(CART).get_data(as_text=True)
    assert f'action="{UPDATE}"' in html
    assert "Zaktualizuj koszyk" in html


def test_cart_page_links_back_to_the_offer(client):
    html = client.get(CART).get_data(as_text=True)
    assert 'href="/oferta"' in html
    assert "Wróć do oferty" in html


def test_cart_page_is_clearly_marked_as_a_stub_demo(client):
    html = client.get(CART).get_data(as_text=True).lower()
    assert "stub" in html
    assert "demonstracyjna" in html


# --- POST /koszyk/aktualizuj ----------------------------------------------


def test_update_route_redirects_back_to_the_cart(client):
    resp = client.post(UPDATE, data={})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(CART)


def test_update_route_flashes_the_fixed_demo_message(client):
    resp = client.post(UPDATE, data={}, follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert FLASH_TEXT in html
    # Rendered through base.html's flash block with the success category.
    assert "flash flash-success" in html


def test_update_route_stub_ignores_submitted_payload(client):
    """The stub does not validate: any payload gets the fixed flash + redirect."""
    resp = client.post(
        UPDATE,
        data={"product_id": "nie-istnieje", "variant_id": "x", "qty": "999"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert FLASH_TEXT in resp.get_data(as_text=True)


def test_fresh_cart_does_not_show_the_update_flash(client):
    """The flash must only appear right after a POST, not on a plain GET."""
    html = client.get(CART).get_data(as_text=True)
    assert FLASH_TEXT not in html


# --- method handling ------------------------------------------------------


def test_update_route_rejects_get(client):
    resp = client.get(UPDATE)
    assert resp.status_code == 405


def test_cart_route_rejects_post(client):
    resp = client.post(CART)
    assert resp.status_code == 405
