"""Tests for M7 (stub): mocked order confirmation.

These validate the current stub deliverable only:
- `stal/templates/confirmation.html` exists and extends `base.html`,
- POST `/zamowienie` renders it as a static "Zamówienie przyjęte" page
  (a demo order number, a `0,00 zł` total, a link back to the homepage),
- GET `/zamowienie` redirects to `/koszyk` (nothing to submit via GET),
- the cart page has a "Złóż zamówienie" form posting to `/zamowienie`,
- the stub route ignores the submitted form: any payload yields the same
  fixed confirmation (no validation, no crash).

The real confirmation (validate non-empty cart + payment + delivery + address,
generate a mock order number and clear the cart) arrives in the real pass and
is tested in `tests/test_routes.py` (not yet written).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "stal" / "templates"

ORDER = "/zamowienie"
CART = "/koszyk"

ORDER_NUMBER = "ZAM-DEMO-0001"
TOTAL = "0,00 zł"


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


def test_confirmation_template_shows_a_demo_order_number():
    tpl = (TEMPLATES / "confirmation.html").read_text(encoding="utf-8")
    assert ORDER_NUMBER in tpl


def test_confirmation_template_shows_a_zero_total():
    tpl = (TEMPLATES / "confirmation.html").read_text(encoding="utf-8")
    assert TOTAL in tpl


def test_confirmation_template_links_back_to_the_homepage():
    tpl = (TEMPLATES / "confirmation.html").read_text(encoding="utf-8")
    assert "url_for('index')" in tpl


# --- POST /zamowienie ------------------------------------------------------


def test_place_order_returns_html(client):
    resp = client.post(ORDER)
    assert resp.status_code == 200
    assert resp.mimetype == "text/html"


def test_place_order_renders_the_confirmation_template(client):
    html = client.post(ORDER).get_data(as_text=True)
    assert "<!doctype html>" in html
    assert '<html lang="pl">' in html
    assert "<h1>Zamówienie przyjęte</h1>" in html


def test_confirmation_page_overrides_the_title_block(client):
    html = client.post(ORDER).get_data(as_text=True)
    assert "<title>Stal — potwierdzenie (stub)</title>" in html


def test_confirmation_page_shows_the_demo_order_number(client):
    html = client.post(ORDER).get_data(as_text=True)
    assert ORDER_NUMBER in html


def test_confirmation_page_shows_a_zero_total(client):
    html = client.post(ORDER).get_data(as_text=True)
    assert TOTAL in html


def test_confirmation_page_is_clearly_marked_as_a_stub_demo(client):
    html = client.post(ORDER).get_data(as_text=True).lower()
    assert "stub" in html
    assert "demonstracyjna" in html


def test_confirmation_page_links_back_to_the_homepage(client):
    html = client.post(ORDER).get_data(as_text=True)
    assert 'href="/"' in html
    assert "Wróć na stronę główną" in html


def test_place_order_stub_ignores_submitted_payload(client):
    """The stub does not validate: any payload gets the same fixed confirmation."""
    resp = client.post(
        ORDER,
        data={"payment_method": "nie-istnieje", "delivery_method": "x", "address": ""},
    )
    assert resp.status_code == 200
    assert "<h1>Zamówienie przyjęte</h1>" in resp.get_data(as_text=True)


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


# --- cart page checkout form ----------------------------------------------


def test_cart_page_has_a_checkout_form_posting_to_order_route(client):
    html = client.get(CART).get_data(as_text=True)
    assert f'action="{ORDER}"' in html
    assert "Złóż zamówienie" in html
