"""Tests for M3 (real): product catalog mock data + lookup helpers.

These validate the real deliverable only:
- `stal/catalog.py` exposes `PRODUCTS`, `get_product` and `get_variant`,
- `PRODUCTS` is a realistic catalog of ~8–10 steel products, each following
  the architecture's data-model shape (`id`, `name`, `category`, `description`,
  `unit`, `variants` with `id`/`label`/`price`),
- fasteners (Elementy złączne) are sold per pack of 100 with quality variants
  (ocynkowana / nierdzewna A2),
- steel profiles (Kształtowniki) are sold per sztanga with 3 m / 6 m length
  variants and a quality encoded in the variant label (S235JR / nierdzewna),
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

FASTENERS = "Elementy złączne"
PROFILES = "Kształtowniki"


# --- PRODUCTS shape -------------------------------------------------------


def test_products_is_a_realistic_list_of_8_to_10_products():
    assert isinstance(PRODUCTS, list)
    assert len(PRODUCTS) >= 8
    assert len(PRODUCTS) <= 10


def test_each_product_follows_the_architecture_data_model_shape():
    for product in PRODUCTS:
        assert isinstance(product, dict)
        assert set(product) == PRODUCT_KEYS
        assert isinstance(product["id"], str) and product["id"]
        assert isinstance(product["name"], str) and product["name"]
        assert isinstance(product["category"], str) and product["category"]
        assert isinstance(product["description"], str) and product["description"]
        assert isinstance(product["unit"], str) and product["unit"]
        assert isinstance(product["variants"], list) and product["variants"]


def test_product_ids_are_unique_and_slug_like():
    ids = [p["id"] for p in PRODUCTS]
    assert len(ids) == len(set(ids))
    for product_id in ids:
        assert product_id == product_id.lower()
        assert " " not in product_id
        # Slugs use only lowercase letters, digits and hyphens.
        assert all(ch.isalnum() or ch == "-" for ch in product_id)


def test_each_variant_follows_the_data_model_shape():
    for product in PRODUCTS:
        for variant in product["variants"]:
            assert isinstance(variant, dict)
            assert set(variant) == VARIANT_KEYS
            assert isinstance(variant["id"], str) and variant["id"]
            assert isinstance(variant["label"], str) and variant["label"]
            assert isinstance(variant["price"], (int, float))
            assert variant["price"] > 0


def test_variant_ids_are_unique_within_each_product():
    for product in PRODUCTS:
        ids = [v["id"] for v in product["variants"]]
        assert len(ids) == len(set(ids))


# --- assortment coverage --------------------------------------------------


def test_catalog_covers_both_expected_categories():
    categories = {p["category"] for p in PRODUCTS}
    assert FASTENERS in categories
    assert PROFILES in categories


def test_fasteners_are_sold_per_pack_of_100():
    fasteners = [p for p in PRODUCTS if p["category"] == FASTENERS]
    assert fasteners
    for product in fasteners:
        assert product["unit"] == "opak. 100 szt."


def test_profiles_are_sold_per_sztanga():
    profiles = [p for p in PRODUCTS if p["category"] == PROFILES]
    assert profiles
    for product in profiles:
        assert product["unit"] == "sztanga"


def test_names_cover_the_owner_brainstorm_assortment():
    """The catalog must demo the families the owner described: screws, nuts,
    washers, self-drilling screws, angles, flat bars, round bars, pipes."""
    all_names = " ".join(p["name"].lower() for p in PRODUCTS)
    for term in (
        "śrub",      # śruba (screw/bolt)
        "nakrętk",   # nakrętka (nut)
        "podkładk",  # podkładka (washer)
        "wkręt",     # wkręt samowiercący (self-drilling screw)
        "kątownik",  # angle
        "płaskownik",  # flat bar
        "pręt",      # round bar / rod
        "rura",      # pipe / tube
    ):
        assert term in all_names, f"missing assortment term: {term}"


def test_fasteners_have_quality_variants():
    """Each fastener offers at least a galvanised and a stainless variant."""
    fasteners = [p for p in PRODUCTS if p["category"] == FASTENERS]
    for product in fasteners:
        labels = [v["label"].lower() for v in product["variants"]]
        assert any("ocynkowana" in label for label in labels)
        assert any("nierdzewna" in label for label in labels)


def test_profiles_have_3m_and_6m_length_variants():
    """Each profile is offered in 3 m and 6 m sztanga lengths."""
    profiles = [p for p in PRODUCTS if p["category"] == PROFILES]
    for product in profiles:
        labels = [v["label"] for v in product["variants"]]
        assert any("3 m" in label for label in labels)
        assert any("6 m" in label for label in labels)


def test_profile_variant_labels_encode_quality():
    """Profile variant labels encode the steel quality (S235JR / nierdzewna)."""
    profiles = [p for p in PRODUCTS if p["category"] == PROFILES]
    for product in profiles:
        for variant in product["variants"]:
            label = variant["label"].lower()
            assert "s235jr" in label or "nierdzewna" in label


def test_catalog_demonstrates_both_structural_and_stainless_quality():
    """Beyond the default S235JR there must be at least one stainless option."""
    all_labels = [
        v["label"].lower()
        for p in PRODUCTS
        if p["category"] == PROFILES
        for v in p["variants"]
    ]
    assert any("s235jr" in label for label in all_labels)
    assert any("nierdzewna" in label for label in all_labels)


def test_longer_bar_costs_more_than_the_shorter_one():
    """For the same quality, the 6 m sztanga must be pricier than 3 m."""
    for product in PRODUCTS:
        if product["category"] != PROFILES:
            continue
        by_quality = {}
        for variant in product["variants"]:
            length, quality = (
                part.strip() for part in variant["label"].split("·", 1)
            )
            by_quality.setdefault(quality, {})[length] = variant["price"]
        for quality, prices in by_quality.items():
            if "3 m" in prices and "6 m" in prices:
                assert prices["6 m"] > prices["3 m"], (
                    f"{product['id']} {quality}: 6 m ({prices['6 m']}) "
                    f"must cost more than 3 m ({prices['3 m']})"
                )


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
        get_variant("nieistniejacy-produkt", "3m-s235jr")
    assert excinfo.value.args[0] == "nieistniejacy-produkt"


def test_get_variant_raises_keyerror_for_unknown_variant_on_known_product():
    product = PRODUCTS[0]
    with pytest.raises(KeyError) as excinfo:
        get_variant(product["id"], "taki-wariant-nie-istnieje")
    assert excinfo.value.args[0] == "taki-wariant-nie-istnieje"


def test_get_variant_is_scoped_to_its_product():
    """A variant id that exists on another product must NOT resolve here."""
    # "3m-nierdzewna" exists only on the round bar; querying it on the angle
    # must raise rather than silently return the wrong product's variant.
    with pytest.raises(KeyError):
        get_variant("katownik-40x40x4", "3m-nierdzewna")
    assert get_variant("pret-okragly-12", "3m-nierdzewna") is not None


# --- module-level sanity --------------------------------------------------


def test_catalog_module_exposes_the_public_api():
    assert catalog.PRODUCTS is PRODUCTS
    assert callable(catalog.get_product)
    assert callable(catalog.get_variant)
