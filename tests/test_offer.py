"""Tests for M4 (real): offer / shop page.

These validate the real deliverable only:
- `stal/templates/shop.html` exists and extends `base.html`,
- GET `/oferta` renders it as a Polish HTML page and shows one product card per
  catalog product (name, category, description, unit),
- every card has a hidden `product_id`, a `variant_id` dropdown listing that
  product's variants with their price, and a `qty` dropdown offering 1..MAX_QTY,
- POST `/oferta/dodaj` validates the submitted product/variant/quantity
  server-side and redirects back to `/oferta` with a Polish success/error flash,
- invalid input never crashes and never leaks to a plain GET,
- GET `/oferta/dodaj` is rejected with 405.
"""

import re
from pathlib import Path

from stal.cart import MAX_QTY
from stal.catalog import PRODUCTS

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "stal" / "templates"

OFFER = "/oferta"
ADD = "/oferta/dodaj"

# A known-good product/variant pair for the success-path tests.
PRODUCT = PRODUCTS[0]
VARIANT = PRODUCT["variants"][0]
QTY = "2"


def _price(value):
    """Mirror the app's ``format_price`` filter (``24,90 zł``)."""
    return f"{value:.2f}".replace(".", ",") + " zł"


def _success_text(product, variant, qty):
    return f"Dodano do koszyka: {product['name']} — {variant['label']} × {qty}."


def _select_block(html, name):
    pattern = re.compile(
        rf'<select[^>]*name="{name}"[^>]*>(.*?)</select>', re.DOTALL
    )
    match = pattern.search(html)
    assert match, f"no <select name={name}> found"
    return match.group(1)


def _options(block):
    return re.findall(r'<option value="([^"]*)"[^>]*>(.*?)</option>', block)


# --- template files -------------------------------------------------------


def test_shop_template_file_exists():
    assert (TEMPLATES / "shop.html").is_file()


def test_shop_template_extends_base_and_fills_content():
    shop = (TEMPLATES / "shop.html").read_text(encoding="utf-8")
    assert '{% extends "base.html" %}' in shop
    assert "{% block content %}" in shop


def test_shop_template_posts_to_add_route_with_dropdowns():
    shop = (TEMPLATES / "shop.html").read_text(encoding="utf-8")
    assert "url_for('add_to_cart')" in shop
    assert 'method="post"' in shop
    assert 'name="product_id"' in shop
    assert 'name="variant_id"' in shop
    assert 'name="qty"' in shop


# --- GET /oferta ----------------------------------------------------------


def test_offer_route_returns_html(client):
    resp = client.get(OFFER)
    assert resp.status_code == 200
    assert resp.mimetype == "text/html"


def test_offer_renders_the_shop_template(client):
    html = client.get(OFFER).get_data(as_text=True)
    assert "<!doctype html>" in html
    assert '<html lang="pl">' in html
    assert "<h1>Oferta</h1>" in html


def test_offer_shows_one_card_per_catalog_product(client):
    html = client.get(OFFER).get_data(as_text=True)
    assert html.count('<article class="product-card">') == len(PRODUCTS)
    assert html.count('<form class="add-to-cart-form"') == len(PRODUCTS)


def test_offer_lists_every_catalog_product_detail(client):
    html = client.get(OFFER).get_data(as_text=True)
    for product in PRODUCTS:
        assert product["name"] in html
        assert product["category"] in html
        assert product["unit"] in html
        assert product["description"] in html


def test_each_card_has_the_correct_hidden_product_id(client):
    html = client.get(OFFER).get_data(as_text=True)
    for product in PRODUCTS:
        expected = (
            '<input type="hidden" name="product_id" value="'
            + product["id"]
            + '">'
        )
        assert expected in html


def test_each_card_has_a_variant_and_quantity_dropdown(client):
    html = client.get(OFFER).get_data(as_text=True)
    assert html.count('name="variant_id"') == len(PRODUCTS)
    assert html.count('name="qty"') == len(PRODUCTS)


def test_each_variant_dropdown_lists_that_products_variants_with_price(client):
    html = client.get(OFFER).get_data(as_text=True)
    for product in PRODUCTS:
        for variant in product["variants"]:
            option = (
                f'<option value="{variant["id"]}">'
                f'{variant["label"]} — {_price(variant["price"])}</option>'
            )
            assert option in html


def test_quantity_dropdown_offers_1_through_max(client):
    html = client.get(OFFER).get_data(as_text=True)
    options = _options(_select_block(html, "qty"))
    expected = [(str(n), str(n)) for n in range(1, MAX_QTY + 1)]
    assert options == expected


def test_offer_shows_polish_price_labels(client):
    html = client.get(OFFER).get_data(as_text=True)
    # A pack price (24,90) and a 6 m sztanga price (124,00) render in Polish.
    assert "24,90 zł" in html
    assert "124,00 zł" in html


def test_offer_is_clearly_marked_as_a_demo(client):
    html = client.get(OFFER).get_data(as_text=True).lower()
    assert "wersja demonstracyjna" in html


def test_offer_no_longer_has_stub_marker(client):
    html = client.get(OFFER).get_data(as_text=True).lower()
    assert "stub" not in html


# --- POST /oferta/dodaj (success) -----------------------------------------


def test_add_route_redirects_back_to_the_offer(client):
    resp = client.post(
        ADD,
        data={
            "product_id": PRODUCT["id"],
            "variant_id": VARIANT["id"],
            "qty": QTY,
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(OFFER)


def test_valid_add_flashes_a_polish_success_message(client):
    resp = client.post(
        ADD,
        data={
            "product_id": PRODUCT["id"],
            "variant_id": VARIANT["id"],
            "qty": QTY,
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert _success_text(PRODUCT, VARIANT, QTY) in html
    assert "flash flash-success" in html


# --- POST /oferta/dodaj (server-side validation) --------------------------


def test_unknown_product_is_rejected(client):
    resp = client.post(
        ADD,
        data={"product_id": "nie-istnieje", "variant_id": VARIANT["id"], "qty": QTY},
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Nieprawidłowy produkt." in html
    assert "flash flash-error" in html


def test_unknown_variant_for_a_known_product_is_rejected(client):
    # "3m-s235jr" exists on the profiles, but not on the screw product.
    resp = client.post(
        ADD,
        data={"product_id": PRODUCT["id"], "variant_id": "3m-s235jr", "qty": QTY},
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Nieprawidłowy wariant produktu." in html
    assert "flash flash-error" in html


def test_missing_payload_is_rejected(client):
    resp = client.post(ADD, data={}, follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Nieprawidłowy produkt." in html
    assert "flash flash-error" in html


def test_non_integer_quantity_is_rejected(client):
    resp = client.post(
        ADD,
        data={"product_id": PRODUCT["id"], "variant_id": VARIANT["id"], "qty": "abc"},
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Ilość musi być liczbą całkowitą." in html
    assert "flash flash-error" in html


def test_zero_quantity_is_rejected(client):
    resp = client.post(
        ADD,
        data={"product_id": PRODUCT["id"], "variant_id": VARIANT["id"], "qty": "0"},
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert f"Ilość musi być liczbą od 1 do {MAX_QTY}." in html


def test_negative_quantity_is_rejected(client):
    resp = client.post(
        ADD,
        data={"product_id": PRODUCT["id"], "variant_id": VARIANT["id"], "qty": "-5"},
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert f"Ilość musi być liczbą od 1 do {MAX_QTY}." in html


def test_quantity_above_max_is_rejected(client):
    resp = client.post(
        ADD,
        data={
            "product_id": PRODUCT["id"],
            "variant_id": VARIANT["id"],
            "qty": str(MAX_QTY + 1),
        },
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert f"Ilość musi być liczbą od 1 do {MAX_QTY}." in html


def test_invalid_add_still_redirects_back_to_the_offer(client):
    resp = client.post(ADD, data={})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(OFFER)


# --- flash isolation ------------------------------------------------------


def test_fresh_offer_does_not_show_the_add_flash(client):
    """The success/error flash must only appear right after a POST."""
    html = client.get(OFFER).get_data(as_text=True)
    assert _success_text(PRODUCT, VARIANT, QTY) not in html
    assert "Nieprawidłowy produkt." not in html


# --- method handling ------------------------------------------------------


def test_add_route_rejects_get(client):
    resp = client.get(ADD)
    assert resp.status_code == 405


# --- format_price filter --------------------------------------------------


def test_format_price_filter_formats_polish_currency(app):
    filter_fn = app.jinja_env.filters["format_price"]
    assert filter_fn(24.9) == "24,90 zł"
    assert filter_fn(124) == "124,00 zł"
    assert filter_fn(0.5) == "0,50 zł"


# --- homepage CTA ---------------------------------------------------------


def test_homepage_links_to_the_offer(client):
    html = client.get("/").get_data(as_text=True)
    assert 'href="/oferta"' in html
