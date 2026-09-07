"""Product catalog (mock data, no database) — real pass.

A small but realistic demo catalog of the steel products the owner sells:

- fasteners (screws, nuts, washers, self-drilling screws) sold per pack of
  100 pieces,
- steel profiles (angle, flat bar, round bar, square tube, channel) sold per
  3 m / 6 m bar ("sztanga") with quality variants.

All data is static Python — no database and no external services. Lookup
helpers raise ``KeyError`` on unknown ids so callers can turn that into a
user-facing error instead of building a broken cart line.
"""

# --- data ------------------------------------------------------------------

PRODUCTS = [
    # --- elementy złączne (opakowania po 100 sztuk) -------------------------
    {
        "id": "sruby-m8x30",
        "name": "Śruba sześciokątna M8×30",
        "category": "Elementy złączne",
        "description": (
            "Śruba z łbem sześciokątnym M8×30 mm, gwint metryczny. "
            "Do standardowych połączeń stalowych."
        ),
        "unit": "opak. 100 szt.",
        "variants": [
            {"id": "ocynkowana", "label": "ocynkowana", "price": 24.90},
            {"id": "nierdzewna-a2", "label": "nierdzewna A2", "price": 59.90},
        ],
    },
    {
        "id": "nakretki-m8",
        "name": "Nakrętka sześciokątna M8",
        "category": "Elementy złączne",
        "description": (
            "Nakrętka sześciokątna M8, gwint metryczny. Pasuje do śrub M8."
        ),
        "unit": "opak. 100 szt.",
        "variants": [
            {"id": "ocynkowana", "label": "ocynkowana", "price": 9.90},
            {"id": "nierdzewna-a2", "label": "nierdzewna A2", "price": 24.90},
        ],
    },
    {
        "id": "podkladki-m8",
        "name": "Podkładka płaska M8",
        "category": "Elementy złączne",
        "description": (
            "Podkładka płaska M8, zwiększa powierzchnię docisku przy "
            "skręcaniu elementów stalowych."
        ),
        "unit": "opak. 100 szt.",
        "variants": [
            {"id": "ocynkowana", "label": "ocynkowana", "price": 6.90},
            {"id": "nierdzewna-a2", "label": "nierdzewna A2", "price": 17.90},
        ],
    },
    {
        "id": "wkrety-samowiercace-48x25",
        "name": "Wkręt samowiercący 4,8×25",
        "category": "Elementy złączne",
        "description": (
            "Wkręt samowiercący 4,8×25 mm z łbem sześciokątnym, do łączenia "
            "blach i profili bez wstępnego wiercenia."
        ),
        "unit": "opak. 100 szt.",
        "variants": [
            {"id": "ocynkowana", "label": "ocynkowana", "price": 18.50},
            {"id": "nierdzewna-a2", "label": "nierdzewna A2", "price": 46.00},
        ],
    },

    # --- kształtowniki (sztangi 3 m / 6 m) ---------------------------------
    {
        "id": "katownik-40x40x4",
        "name": "Kątownik 40×40×4 mm",
        "category": "Kształtowniki",
        "description": (
            "Kątownik stalowy równoramienny 40×40×4 mm ze stali "
            "konstrukcyjnej S235JR."
        ),
        "unit": "sztanga",
        "variants": [
            {"id": "3m-s235jr", "label": "3 m · S235JR", "price": 62.00},
            {"id": "6m-s235jr", "label": "6 m · S235JR", "price": 124.00},
        ],
    },
    {
        "id": "plaskownik-40x4",
        "name": "Płaskownik 40×4 mm",
        "category": "Kształtowniki",
        "description": (
            "Płaskownik stalowy 40×4 mm ze stali konstrukcyjnej S235JR."
        ),
        "unit": "sztanga",
        "variants": [
            {"id": "3m-s235jr", "label": "3 m · S235JR", "price": 38.00},
            {"id": "6m-s235jr", "label": "6 m · S235JR", "price": 76.00},
        ],
    },
    {
        "id": "pret-okragly-12",
        "name": "Pręt okrągły Ø12 mm",
        "category": "Kształtowniki",
        "description": (
            "Pręt stalowy okrągły Ø12 mm, gładki, do zbrojeń i konstrukcji."
        ),
        "unit": "sztanga",
        "variants": [
            {"id": "3m-s235jr", "label": "3 m · S235JR", "price": 29.00},
            {"id": "6m-s235jr", "label": "6 m · S235JR", "price": 58.00},
            {"id": "3m-nierdzewna", "label": "3 m · nierdzewna", "price": 145.00},
        ],
    },
    {
        "id": "rura-kwadratowa-40x40x3",
        "name": "Rura kwadratowa 40×40×3 mm",
        "category": "Kształtowniki",
        "description": (
            "Rura stalowa kwadratowa 40×40 mm, grubość ścianki 3 mm, "
            "ze stali konstrukcyjnej S235JR."
        ),
        "unit": "sztanga",
        "variants": [
            {"id": "3m-s235jr", "label": "3 m · S235JR", "price": 89.00},
            {"id": "6m-s235jr", "label": "6 m · S235JR", "price": 178.00},
        ],
    },
    {
        "id": "ceownik-80x45x6",
        "name": "Ceownik 80×45×6 mm",
        "category": "Kształtowniki",
        "description": (
            "Ceownik stalowy 80×45×6 mm ze stali konstrukcyjnej S235JR."
        ),
        "unit": "sztanga",
        "variants": [
            {"id": "3m-s235jr", "label": "3 m · S235JR", "price": 105.00},
            {"id": "6m-s235jr", "label": "6 m · S235JR", "price": 210.00},
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
