"""Tests for M3 (stub): product catalog mock data + lookup helpers.

These validate the current stub deliverable only:
- `stal/catalog.py` exposes `PRODUCTS`, `get_product` and `get_variant`,
- `PRODUCTS` is a list of exactly 2 hardcoded products (one variant each),
  each following the architecture's data-model shape,
- `get_product` returns the right dict and raises `KeyError` on unknown ids,
- `get_variant` returns the variant scoped to its product and raises
  `KeyError` on unknown product or variant (including a variant that exists
  on a *different* product).
"""

import pytest

from stal import catalog
from stal.catalog import PRODUCTS, get_product, get_variant

# Keys every product dict must expose, per the architecture data model.
PRODUCT_KEYS = {"id", "name", "category", "description", "unit", "variants"}
VARIANT_KEYS = {"id", "label", "price"}


# --- PRODUCTS shape -------------------------------------------------------


def test_products_is_a_list_of_exactly_two_stub_products():
    assert isinstance(PRODUCTS, list)
    assert len(PRODUCTS) == 2


def test_each_product_follows_the_architecture_data_model_shape():
    for product in PRODUCTS:
        assert isinstance(product, dict)
        assert set(product) == PRODUCT_KEYS
        assert isinstance(product["id"], str) and product["id"]
        assert isinstance(product["name"], str) and product["name"]
        assert isinstance(product["category"], str) and product["category"]
        assert isinstance(product["description"], str) and product["description"]
        assert isinstance(product["unit"], str) and product["unit"]
        assert isinstance(product["variants"], list)


def test_product_ids_are_unique():
    ids = [p["id"] for p in PRODUCTS]
    assert len(ids) == len(set(ids))


def test_each_stub_product_has_exactly_one_variant():
    for product in PRODUCTS:
        assert len(product["variants"]) == 1


def test_each_variant_follows_the_data_model_shape():
    for product in PRODUCTS:
        for variant in product["variants"]:
            assert isinstance(variant, dict)
            assert set(variant) == VARIANT_KEYS
            assert isinstance(variant["id"], str) and variant["id"]
            assert isinstance(variant["label"], str) and variant["label"]
            assert isinstance(variant["price"], (int, float))
            assert variant["price"] > 0


def test_stub_catalog_covers_both_expected_categories():
    # The stub must demonstrate the two shop families the owner described:
    # a fastener sold per pack and a steel profile sold per sztanga.
    units = {p["unit"] for p in PRODUCTS}
    categories = {p["category"] for p in PRODUCTS}
    assert "opak. 100 szt." in units
    assert "sztanga" in units
    assert "Elementy złączne" in categories
    assert "Kształtowniki" in categories


# --- get_product ----------------------------------------------------------


def test_get_product_returns_the_exact_dict_for_known_ids():
    for product in PRODUCTS:
        assert get_product(product["id"]) is product


def test_get_product_raises_keyerror_for_unknown_id():
    with pytest.raises(KeyError) as excinfo:
        get_product("nieistniejacy-produkt")
    assert excinfo.value.args[0] == "nieistniejacy-produkt"


def test_get_product_rejects_empty_and_none_ids():
    for bad in ("", None):
        with pytest.raises(KeyError):
            get_product(bad)


# --- get_variant ----------------------------------------------------------


def test_get_variant_returns_the_exact_dict_for_known_pairs():
    for product in PRODUCTS:
        for variant in product["variants"]:
            assert get_variant(product["id"], variant["id"]) is variant


def test_get_variant_raises_keyerror_for_unknown_product():
    with pytest.raises(KeyError) as excinfo:
        get_variant("nieistniejacy-produkt", "ocynkowana")
    assert excinfo.value.args[0] == "nieistniejacy-produkt"


def test_get_variant_raises_keyerror_for_unknown_variant_on_known_product():
    product = PRODUCTS[0]
    with pytest.raises(KeyError) as excinfo:
        get_variant(product["id"], "taki-wariant-nie-istnieje")
    assert excinfo.value.args[0] == "taki-wariant-nie-istnieje"


def test_get_variant_is_scoped_to_its_product():
    """A variant id that exists on another product must NOT resolve here."""
    first_product, second_product = PRODUCTS[0], PRODUCTS[1]
    first_variant = first_product["variants"][0]["id"]
    with pytest.raises(KeyError):
        get_variant(second_product["id"], first_variant)


# --- module-level sanity --------------------------------------------------


def test_catalog_module_exposes_the_public_api():
    assert catalog.PRODUCTS is PRODUCTS
    assert callable(catalog.get_product)
    assert callable(catalog.get_variant)
