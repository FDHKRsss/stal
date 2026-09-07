"""Tests for M8 (real): styling & UX polish.

These validate the real deliverable only:
- `stal/static/style.css` is a presentable stylesheet — it is served at
  `/static/style.css` (HTTP 200, `text/css`) and it actually styles the
  semantic classes the templates already emit (no leftover "stub pass"
  comment): the `product-grid` / `product-card` offer cards, the
  `cart-lines` / `order-lines` tables, the `checkout-form` and the
  `demo-note` callouts,
- `base.html` provides the shared layout shell (header with brand + nav +
  `cart-count` badge, flash block, stylesheet link, footer) and that shell
  renders consistently on every page,
- the offer, summary and confirmation pages render those semantic classes.
"""

from pathlib import Path

from stal.cart import add_item
from stal.catalog import get_product, get_variant

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "stal" / "static"
TEMPLATES = ROOT / "stal" / "templates"

P1 = get_product("sruby-m8x30")
V1 = get_variant("sruby-m8x30", "ocynkowana")


def _css():
    return (STATIC / "style.css").read_text(encoding="utf-8")


def _seed_cart(client, qty=2):
    with client.session_transaction() as sess:
        add_item(sess, P1["id"], V1["id"], qty)


# --- files ---------------------------------------------------------------


def test_stylesheet_file_exists():
    assert (STATIC / "style.css").is_file()


def test_stylesheet_is_a_real_stylesheet_not_a_stub():
    css = _css()
    # The "stub pass" header comment must be gone and the real semantic
    # classes must all have rules.
    assert "stub" not in css.lower()
    for selector in (
        ".site-header",
        ".cart-count",
        ".flashes",
        ".flash-success",
        ".flash-error",
        ".product-grid",
        ".product-card",
        ".add-to-cart-form",
        ".cart-lines",
        ".checkout-form",
        ".order-lines",
        ".demo-note",
        ".button",
        ".site-footer",
    ):
        assert selector in css, f"missing {selector!r} rule"


def test_base_template_links_to_the_stylesheet():
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert "url_for('static', filename='style.css')" in base


# --- static route --------------------------------------------------------


def test_stylesheet_is_served_as_css(client):
    resp = client.get("/static/style.css")
    assert resp.status_code == 200
    assert resp.mimetype == "text/css"
    assert ".product-grid" in resp.get_data(as_text=True)
    assert ".checkout-form" in resp.get_data(as_text=True)


# --- shared layout shell --------------------------------------------------


def test_homepage_renders_shared_nav_and_footer(client):
    html = client.get("/").get_data(as_text=True)
    assert '<header class="site-header">' in html
    assert 'href="/oferta"' in html
    assert 'href="/koszyk"' in html
    assert "Oferta" in html
    assert "Koszyk" in html
    assert "<footer" in html


def test_nav_cart_count_badge_renders_on_every_page(client):
    for path in ("/", "/oferta", "/koszyk"):
        html = client.get(path).get_data(as_text=True)
        assert '<span class="cart-count">0</span>' in html


def test_homepage_links_to_stylesheet(client):
    html = client.get("/").get_data(as_text=True)
    assert 'href="/static/style.css"' in html


def test_flash_renders_within_shared_layout(client):
    resp = client.post(
        "/oferta/dodaj",
        data={
            "product_id": P1["id"],
            "variant_id": V1["id"],
            "qty": "1",
        },
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Dodano do koszyka:" in html
    assert "flash flash-success" in html
    assert '<header class="site-header">' in html
    assert "<footer" in html


# --- rendered semantic classes -------------------------------------------


def test_offer_renders_product_grid_and_cards(client):
    html = client.get("/oferta").get_data(as_text=True)
    assert 'class="product-grid"' in html
    assert '<article class="product-card">' in html
    assert '<form class="add-to-cart-form"' in html


def test_summary_renders_the_checkout_form(client):
    html = client.get("/koszyk").get_data(as_text=True)
    assert '<form method="post" action="/zamowienie" class="checkout-form">' in html


def test_populated_summary_renders_the_cart_lines_table(client):
    _seed_cart(client)
    html = client.get("/koszyk").get_data(as_text=True)
    assert '<table class="cart-lines">' in html


def test_confirmation_renders_the_order_lines_table(client):
    _seed_cart(client, qty=1)
    resp = client.post(
        "/zamowienie",
        data={
            "payment_method": "przelew",
            "delivery_method": "odbior",
            "address": "",
        },
    )
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "<h1>Zamówienie przyjęte</h1>" in html
    assert '<table class="order-lines">' in html


def test_demo_note_renders_on_homepage_and_confirmation(client):
    html = client.get("/").get_data(as_text=True)
    assert 'class="demo-note"' in html

    _seed_cart(client, qty=1)
    html = client.post(
        "/zamowienie",
        data={
            "payment_method": "przelew",
            "delivery_method": "odbior",
            "address": "",
        },
    ).get_data(as_text=True)
    assert 'class="demo-note"' in html


# --- context processor ---------------------------------------------------


def test_cart_count_is_available_to_templates(app):
    from flask import render_template_string

    with app.test_request_context("/"):
        assert render_template_string("{{ cart_count }}") == "0"
