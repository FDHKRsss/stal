"""Tests for the cart logic (M9).

Stub pass — one smoke test: the `stal.cart` module is importable and wired to
the documented public API, and the stub readers return their fixed/empty
values. The real, session-backed behavior (add / merge / update / remove /
quantity & product validation / totals) arrives in the real pass and will be
tested here.
"""

from stal import cart


def test_cart_module_is_wired_end_to_end():
    """Smoke test: the cart module exposes its API and works in the stub."""
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
        assert hasattr(cart, name), f"cart.{name} is missing"
        assert callable(getattr(cart, name)), f"cart.{name} is not callable"

    assert cart.get_cart(None) == []
    assert cart.cart_lines(None) == []
    assert cart.cart_total(None) == 0.0
    assert cart.cart_count(None) == 0
