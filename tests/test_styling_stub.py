"""Tests for M8 (stub): styling & UX polish.

These validate the current stub deliverable only:
- `stal/static/style.css` exists and is served at `/static/style.css`
  (HTTP 200, `text/css`),
- `base.html` provides the shared layout shell: a header with a brand and
  nav links (Oferta / Koszyk) plus a `cart-count` badge, a flash-message
  block, a stylesheet link and a footer,
- the nav/footer and the `0` cart badge render on every page,
- the cart badge is wired through a context processor to the documented
  `cart_count(session)` helper (which returns `0` in the stub).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "stal" / "static"
TEMPLATES = ROOT / "stal" / "templates"


# --- files ---------------------------------------------------------------


def test_stylesheet_file_exists():
    assert (STATIC / "style.css").is_file()


def test_base_template_links_to_the_stylesheet():
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert "url_for('static', filename='style.css')" in base


def test_base_template_has_shared_header_and_nav():
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert "<header" in base
    assert "<nav" in base


def test_base_template_has_nav_links_and_cart_badge():
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert "url_for('index')" in base
    assert "url_for('offer')" in base
    assert "url_for('cart')" in base
    assert "cart-count" in base
    assert "{{ cart_count }}" in base


def test_base_template_renders_flash_messages():
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert "get_flashed_messages" in base
    assert "{% for category, message in messages %}" in base


def test_base_template_has_footer():
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert "<footer" in base


# --- static route --------------------------------------------------------


def test_stylesheet_is_served_as_css(client):
    resp = client.get("/static/style.css")
    assert resp.status_code == 200
    assert resp.mimetype == "text/css"
    assert ".site-header" in resp.get_data(as_text=True)


# --- rendered shared layout ----------------------------------------------


def test_homepage_renders_shared_nav(client):
    html = client.get("/").get_data(as_text=True)
    assert '<header class="site-header">' in html
    assert 'href="/oferta"' in html
    assert 'href="/koszyk"' in html
    assert "Oferta" in html
    assert "Koszyk" in html


def test_homepage_renders_cart_count_badge(client):
    html = client.get("/").get_data(as_text=True)
    assert '<span class="cart-count">0</span>' in html


def test_homepage_renders_footer(client):
    html = client.get("/").get_data(as_text=True)
    assert "<footer" in html
    assert "Wersja demonstracyjna" in html


def test_homepage_links_to_stylesheet(client):
    html = client.get("/").get_data(as_text=True)
    assert 'href="/static/style.css"' in html


def test_nav_and_footer_are_shared_across_pages(client):
    for path in ("/", "/oferta", "/koszyk"):
        html = client.get(path).get_data(as_text=True)
        assert '<header class="site-header">' in html
        assert '<span class="cart-count">0</span>' in html
        assert "<footer" in html


def test_flash_renders_within_shared_layout(client):
    resp = client.post("/koszyk/aktualizuj", data={}, follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Koszyk zaktualizowany (wersja demonstracyjna)." in html
    assert "flash flash-success" in html
    # The shared header/nav and footer still surround the flash block.
    assert '<header class="site-header">' in html
    assert "<footer" in html


# --- context processor ---------------------------------------------------


def test_cart_count_is_available_to_templates(app):
    from flask import render_template_string

    with app.test_request_context("/"):
        assert render_template_string("{{ cart_count }}") == "0"
