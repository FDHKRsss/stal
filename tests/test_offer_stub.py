"""Tests for M4 (stub): offer / shop page.

These validate the current stub deliverable only:
- `stal/templates/shop.html` exists and extends `base.html`,
- GET `/oferta` renders it (HTML) and lists the product names + units,
- the per-product "add to cart" form posts to `/oferta/dodaj`,
- POST `/oferta/dodaj` flashes a fixed demo message and redirects back to
  `/oferta` (the stub ignores the submitted form),
- the flash message is actually rendered and does not leak to a fresh GET,
- the homepage CTA links to `/oferta`.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "stal" / "templates"

OFFER = "/oferta"
ADD = "/oferta/dodaj"
FLASH_TEXT = "Dodano do koszyka (wersja demonstracyjna)."


# --- template files -------------------------------------------------------


def test_shop_template_file_exists():
    assert (TEMPLATES / "shop.html").is_file()


def test_shop_template_extends_base_and_fills_content():
    shop = (TEMPLATES / "shop.html").read_text(encoding="utf-8")
    assert '{% extends "base.html" %}' in shop
    assert "{% block content %}" in shop


def test_shop_template_posts_to_the_add_route():
    shop = (TEMPLATES / "shop.html").read_text(encoding="utf-8")
    assert "url_for('add_to_cart')" in shop
    assert 'method="post"' in shop
    assert 'name="product_id"' in shop


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


def test_offer_lists_every_catalog_product_name(client):
    from stal.catalog import PRODUCTS

    html = client.get(OFFER).get_data(as_text=True)
    for product in PRODUCTS:
        assert product["name"] in html


def test_offer_lists_every_catalog_product_unit(client):
    from stal.catalog import PRODUCTS

    html = client.get(OFFER).get_data(as_text=True)
    for product in PRODUCTS:
        assert product["unit"] in html


def test_offer_shows_an_add_to_cart_form_for_each_product(client):
    from stal.catalog import PRODUCTS

    html = client.get(OFFER).get_data(as_text=True)
    assert html.count('action="' + ADD + '"') == len(PRODUCTS)
    assert html.count("Dodaj do koszyka") == len(PRODUCTS)


def test_offer_is_clearly_marked_as_a_stub_demo(client):
    html = client.get(OFFER).get_data(as_text=True).lower()
    assert "stub" in html
    assert "demonstracyjna" in html


# --- POST /oferta/dodaj ---------------------------------------------------


def test_add_route_redirects_back_to_the_offer(client):
    resp = client.post(ADD, data={"product_id": "sruby-m8x30"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(OFFER)


def test_add_route_flashes_the_fixed_demo_message(client):
    resp = client.post(ADD, data={"product_id": "sruby-m8x30"}, follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert FLASH_TEXT in html
    # Rendered through base.html's flash block with the success category.
    assert "flash flash-success" in html


def test_add_route_stub_ignores_unknown_product_ids(client):
    """The stub does not validate: any payload gets the fixed flash + redirect."""
    resp = client.post(ADD, data={"product_id": "nie-istnieje"}, follow_redirects=True)
    assert resp.status_code == 200
    assert FLASH_TEXT in resp.get_data(as_text=True)


def test_add_route_stub_ignores_missing_payload(client):
    resp = client.post(ADD, data={}, follow_redirects=True)
    assert resp.status_code == 200
    assert FLASH_TEXT in resp.get_data(as_text=True)


def test_fresh_offer_does_not_show_the_add_flash(client):
    """The flash must only appear right after a POST, not on a plain GET."""
    html = client.get(OFFER).get_data(as_text=True)
    assert FLASH_TEXT not in html


def test_add_route_rejects_get(client):
    resp = client.get(ADD)
    assert resp.status_code == 405


# --- homepage CTA ---------------------------------------------------------


def test_homepage_links_to_the_offer(client):
    html = client.get("/").get_data(as_text=True)
    assert 'href="' + OFFER + '"' in html
