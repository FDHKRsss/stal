"""Product catalog (mock data, no database) — stub pass.

The stub provides two hardcoded products with a single variant each, so the
catalog module and its lookup helpers exist and can be imported end-to-end.
The realistic ~8-10 product catalog arrives in the real pass.
"""

# --- data ------------------------------------------------------------------

PRODUCTS = [
    {
        "id": "sruby-m8x30",
        "name": "Śruba sześciokątna M8×30",
        "category": "Elementy złączne",
        "description": "Śruba sześciokątna M8×30 mm ze stali ocynkowanej.",
        "unit": "opak. 100 szt.",
        "variants": [
            {"id": "ocynkowana", "label": "ocynkowana", "price": 24.90},
        ],
    },
    {
        "id": "katownik-40x40x4",
        "name": "Kątownik 40×40×4 mm",
        "category": "Kształtowniki",
        "description": "Kątownik stalowy równoramienny 40×40×4 mm.",
        "unit": "sztanga",
        "variants": [
            {"id": "3m-s235jr", "label": "3 m · S235JR", "price": 62.00},
        ],
    },
]


# --- lookup helpers --------------------------------------------------------

def get_product(product_id):
    """Return the product dict for ``product_id``.

    Raises ``KeyError`` when the id is unknown, so callers can turn it into a
    user-facing error instead of silently producing a broken cart line.
    """
    for product in PRODUCTS:
        if product["id"] == product_id:
            return product
    raise KeyError(product_id)


def get_variant(product_id, variant_id):
    """Return the variant dict for ``variant_id`` of ``product_id``.

    Raises ``KeyError`` when the product or the variant is unknown.
    """
    product = get_product(product_id)
    for variant in product["variants"]:
        if variant["id"] == variant_id:
            return variant
    raise KeyError(variant_id)
