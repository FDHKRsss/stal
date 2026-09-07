"""Tests for M9 (real): route flow & robustness.

These validate the full user journey through the Flask test client —
``/`` -> ``/oferta`` -> add -> ``/koszyk`` -> update -> ``/zamowienie`` —
together with the cross-cutting error/validation cases that make the mock
robust: unknown product/variant/quantity input, wrong HTTP methods, a
tampered session cookie, unknown routes and the safe handling of invalid
order payloads. No test here binds a host port; everything goes through the
``client`` fixture (a Flask test client), so the suite never depends on a
free port.
"""

import re

import pytest
from flask import Flask

from stal.cart import MAX_QTY, cart_count
from stal.catalog import PRODUCTS, get_product, get_variant

HOME = "/"
OFFER = "/oferta"
ADD = "/oferta/dodaj"
CART = "/koszyk"
UPDATE = "/koszyk/aktualizuj"
ORDER = "/zamowienie"
HEALTH = "/health"

# Known-good catalog ids used to seed a cart through the real add route.
P1 = get_product("sruby-m8x30")
V1 = get_variant("sruby-m8x30", "ocynkowana")
P2 = get_product("katownik-40x40x4")
V2 = get_variant("katownik-40x40x4", "3m-s235jr")


def _price(value):
    """Mirror the app's ``format_price`` filter (``24,90 zł``)."""
    return f"{value:.2f}".replace(".", ",") + " zł"


def _add(client, product_id, variant_id, qty, **kwargs):
    return client.post(
        ADD,
        data={"product_id": product_id, "variant_id": variant_id, "qty": str(qty)},
        **kwargs,
    )


def _valid_order(**overrides):
    data = {
        "payment_method": "przelew",
        "delivery_method": "kurier",
        "address": "ul. Stalowa 1, 00-001 Warszawa",
    }
    data.update(overrides)
    return data


def _session_cart(client):
    """Return the current signed-session cart as plain Python data."""
    with client.session_transaction() as sess:
        return list(sess.get("cart", []))


def _line(product_id, variant_id, qty):
    return {"product_id": product_id, "variant_id": variant_id, "qty": qty}


# --- app factory / health smoke ------------------------------------------


def test_app_factory_builds_a_flask_app(app):
    assert isinstance(app, Flask)


def test_health_returns_json_status_ok(client):
    resp = client.get(HEALTH)
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    assert resp.get_json() == {"status": "ok"}


def test_every_documented_endpoint_is_registered(app):
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    for path in (HOME, OFFER, ADD, CART, UPDATE, ORDER, HEALTH):
        assert path in rules


# --- public pages ---------------------------------------------------------


def test_homepage_renders_polish_description_and_cta(client):
    resp = client.get(HOME)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert '<html lang="pl">' in html
    assert "O nas" in html
    assert "Przejdź do oferty" in html
    assert 'href="/oferta"' in html
    assert "wersja demonstracyjna" in html.lower()


@pytest.mark.parametrize("path", [HOME, OFFER, CART])
def test_every_public_page_renders_the_polish_shell(client, path):
    resp = client.get(path)
    assert resp.status_code == 200
    assert resp.mimetype == "text/html"
    html = resp.get_data(as_text=True)
    assert '<html lang="pl">' in html
    assert "<footer" in html


# --- full happy-path flow -------------------------------------------------


def test_full_checkout_flow_end_to_end(client):
    # 1. The journey starts on the homepage.
    resp = client.get(HOME)
    assert resp.status_code == 200
    assert "O nas" in resp.get_data(as_text=True)

    # 2. The offer lists every catalog product.
    resp = client.get(OFFER)
    assert resp.status_code == 200
    assert resp.get_data(as_text=True).count('<article class="product-card">') == len(PRODUCTS)

    # 3. Add two distinct lines through the real add route.
    resp = _add(client, P1["id"], V1["id"], 2)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(OFFER)
    _add(client, P2["id"], V2["id"], 1)
    assert _session_cart(client) == [
        _line(P1["id"], V1["id"], 2),
        _line(P2["id"], V2["id"], 1),
    ]

    # 4. The shared nav badge reflects the real unit count.
    html = client.get(OFFER).get_data(as_text=True)
    assert '<span class="cart-count">3</span>' in html

    # 5. The summary renders both lines and the correct grand total.
    html = client.get(CART).get_data(as_text=True)
    assert P1["name"] in html and V1["label"] in html
    assert P2["name"] in html and V2["label"] in html
    total = round(V1["price"] * 2 + V2["price"] * 1, 2)
    assert f"Razem do zapłaty: {_price(total)}" in html

    # 6. Update one line's quantity through the real update route.
    resp = client.post(
        UPDATE,
        data={"action": "update", "product_id": P1["id"], "variant_id": V1["id"], "qty": "4"},
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(CART)
    html = client.get(CART).get_data(as_text=True)
    assert '<input type="number" name="qty" value="4" min="1" max="99">' in html
    total = round(V1["price"] * 4 + V2["price"] * 1, 2)
    assert f"Razem do zapłaty: {_price(total)}" in html
    assert '<span class="cart-count">5</span>' in html

    # 7. Place the order (delivery with an address) and see the confirmation.
    resp = client.post(ORDER, data=_valid_order())
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "<h1>Zamówienie przyjęte</h1>" in html
    assert re.search(r"ZAM-\d{8}-\d{6}", html) is not None
    assert "przelew bankowy (przedpłata)" in html
    assert "dostawa kurierem" in html
    assert "ul. Stalowa 1, 00-001 Warszawa" in html
    assert f"Razem do zapłaty: {_price(total)}" in html

    # 8. A successful order clears the cart.
    assert _session_cart(client) == []


def test_pickup_checkout_flow_without_an_address(client):
    _add(client, P1["id"], V1["id"], 3)
    resp = client.post(
        ORDER,
        data=_valid_order(delivery_method="odbior", address=""),
    )
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "<h1>Zamówienie przyjęte</h1>" in html
    assert "odbiór osobisty (magazyn)" in html
    assert "ul. Stalowa 1, 00-001 Warszawa" not in html
    assert _session_cart(client) == []


# --- granular route transitions -------------------------------------------


def test_add_redirects_to_the_offer_and_persists_the_cart(client):
    resp = _add(client, P1["id"], V1["id"], 3)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(OFFER)
    assert _session_cart(client) == [_line(P1["id"], V1["id"], 3)]


def test_update_redirects_to_the_cart(client):
    _add(client, P1["id"], V1["id"], 1)
    resp = client.post(
        UPDATE,
        data={"action": "update", "product_id": P1["id"], "variant_id": V1["id"], "qty": "9"},
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(CART)
    assert _session_cart(client) == [_line(P1["id"], V1["id"], 9)]


def test_remove_redirects_to_the_cart_and_empties_it(client):
    _add(client, P1["id"], V1["id"], 1)
    resp = client.post(
        UPDATE,
        data={"action": "remove", "product_id": P1["id"], "variant_id": V1["id"]},
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(CART)
    assert _session_cart(client) == []


def test_get_order_redirects_to_the_cart(client):
    resp = client.get(ORDER)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(CART)


# --- validation & error handling -----------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"product_id": "nie-istnieje", "variant_id": V1["id"], "qty": "1"},
        {"product_id": P1["id"], "variant_id": "nie-istnieje", "qty": "1"},
        {"product_id": P1["id"], "variant_id": V1["id"], "qty": "abc"},
        {"product_id": P1["id"], "variant_id": V1["id"], "qty": "0"},
        {"product_id": P1["id"], "variant_id": V1["id"], "qty": str(MAX_QTY + 1)},
    ],
)
def test_invalid_add_never_crashes_and_redirects_to_the_offer(client, payload):
    resp = client.post(ADD, data=payload)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(OFFER)
    assert _session_cart(client) == []


def test_order_rejects_an_empty_cart(client):
    resp = client.post(ORDER, data=_valid_order(), follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Twój koszyk jest pusty." in html
    assert "<h1>Koszyk</h1>" in html
    assert "<h1>Zamówienie przyjęte</h1>" not in html


def test_order_rejects_unknown_payment_without_losing_the_cart(client):
    _add(client, P1["id"], V1["id"], 1)
    resp = client.post(
        ORDER, data=_valid_order(payment_method="nieznany"), follow_redirects=True
    )
    assert resp.status_code == 200
    assert "Wybierz prawidłowy sposób płatności." in resp.get_data(as_text=True)
    assert _session_cart(client) == [_line(P1["id"], V1["id"], 1)]


def test_order_requires_an_address_for_delivery(client):
    _add(client, P1["id"], V1["id"], 1)
    resp = client.post(
        ORDER, data=_valid_order(delivery_method="kurier", address=""), follow_redirects=True
    )
    assert resp.status_code == 200
    assert "Podaj adres dostawy" in resp.get_data(as_text=True)
    assert _session_cart(client) == [_line(P1["id"], V1["id"], 1)]


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", ADD),
        ("get", UPDATE),
        ("post", HOME),
        ("post", OFFER),
        ("post", CART),
    ],
)
def test_wrong_http_method_returns_405(client, method, path):
    resp = getattr(client, method)(path)
    assert resp.status_code == 405


def test_unknown_route_returns_a_polish_404(client):
    resp = client.get("/taka-strona-nie-istnieje")
    assert resp.status_code == 404
    html = resp.get_data(as_text=True)
    assert "Nie znaleziono strony" in html


def test_tampered_session_cookie_behaves_like_an_empty_cart(client):
    # A forged/invalid signed cookie must degrade to an empty session (Flask
    # catches ``BadSignature``), never a 400/500.
    client.set_cookie("session", "sfalszowana-wartosc.nieprawidlowy-podpis")
    resp = client.get(CART)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Koszyk jest pusty." in html
    assert "Razem do zapłaty: 0,00 zł" in html
    assert '<span class="cart-count">0</span>' in html
    with client.session_transaction() as sess:
        assert cart_count(sess) == 0
