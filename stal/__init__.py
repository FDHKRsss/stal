"""Flask application factory for the steel mock e-shop."""

from datetime import datetime

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from stal.cart import (
    MAX_QTY,
    add_item,
    cart_count,
    cart_lines,
    clear_cart,
    remove_item,
    update_item,
)
from stal.catalog import PRODUCTS, get_product, get_variant
from stal.config import Config

# Mocked checkout options (no real payment/order integration). The keys are
# what the forms submit; the values are the Polish labels shown to the owner.
PAYMENT_METHODS = {
    "przelew": "przelew bankowy (przedpłata)",
    "karta": "karta płatnicza online",
    "gotowka": "gotówka przy odbiorze",
    "odroczony": "przelew z odroczonym terminem (dla firm)",
}

DELIVERY_METHODS = {
    "odbior": "odbiór osobisty (magazyn)",
    "kurier": "dostawa kurierem",
    "transport": "dostawa transportem własnym",
}

# The only delivery option that does not require an address.
PICKUP_DELIVERY = "odbior"


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.template_filter("format_price")
    def format_price(value):
        """Format a price as Polish currency, e.g. ``24,90 zł``."""
        return f"{value:.2f}".replace(".", ",") + " zł"

    @app.context_processor
    def inject_cart_count():
        # The shared nav badge renders the real cart unit count from the
        # session-backed cart (M5 -- real).
        return {"cart_count": cart_count(session)}

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/oferta")
    def offer():
        return render_template("shop.html", products=PRODUCTS, max_qty=MAX_QTY)

    @app.post("/oferta/dodaj")
    def add_to_cart():
        # Real pass: validate the submitted product/variant/quantity against
        # the catalog before handing it to the cart helper. Invalid input never
        # crashes — it flashes a Polish message and returns to the offer.
        product_id = request.form.get("product_id", "").strip()
        variant_id = request.form.get("variant_id", "").strip()
        qty_raw = request.form.get("qty", "").strip()

        try:
            product = get_product(product_id)
        except KeyError:
            flash("Nieprawidłowy produkt.", "error")
            return redirect(url_for("offer"))

        try:
            variant = get_variant(product_id, variant_id)
        except KeyError:
            flash("Nieprawidłowy wariant produktu.", "error")
            return redirect(url_for("offer"))

        try:
            qty = int(qty_raw)
        except (TypeError, ValueError):
            flash("Ilość musi być liczbą całkowitą.", "error")
            return redirect(url_for("offer"))

        if qty < 1 or qty > MAX_QTY:
            flash(f"Ilość musi być liczbą od 1 do {MAX_QTY}.", "error")
            return redirect(url_for("offer"))

        add_item(session, product_id, variant_id, qty)
        flash(
            f"Dodano do koszyka: {product['name']} — {variant['label']} × {qty}.",
            "success",
        )
        return redirect(url_for("offer"))

    @app.get("/koszyk")
    def cart():
        # Real pass: render the live session-backed cart lines and their
        # totals, together with the mocked payment/delivery selectors. A broken
        # (stale/tampered) cart line is dropped instead of crashing the demo.
        try:
            lines = cart_lines(session)
        except KeyError:
            clear_cart(session)
            flash(
                "Koszyk zawierał nieaktualne pozycje i został wyczyszczony.",
                "error",
            )
            return redirect(url_for("offer"))

        total = round(sum(line["line_total"] for line in lines), 2)
        return render_template(
            "cart.html",
            lines=lines,
            total=total,
            payment_methods=PAYMENT_METHODS,
            delivery_methods=DELIVERY_METHODS,
            pickup_delivery=PICKUP_DELIVERY,
            max_qty=MAX_QTY,
        )

    @app.post("/koszyk/aktualizuj")
    def update_cart():
        # Real pass: update one line's quantity or remove that line. Each form
        # posts its own ``product_id``/``variant_id`` (plus ``qty`` for updates
        # and an ``action`` switch for removals). Invalid quantity input never
        # crashes — it flashes a Polish message and returns to the summary.
        action = request.form.get("action", "update").strip()
        product_id = request.form.get("product_id", "").strip()
        variant_id = request.form.get("variant_id", "").strip()

        if action == "remove":
            remove_item(session, product_id, variant_id)
            flash("Usunięto pozycję z koszyka.", "success")
            return redirect(url_for("cart"))

        qty_raw = request.form.get("qty", "").strip()
        try:
            qty = int(qty_raw)
        except (TypeError, ValueError):
            flash("Ilość musi być liczbą całkowitą.", "error")
            return redirect(url_for("cart"))

        if qty < 1 or qty > MAX_QTY:
            flash(f"Ilość musi być liczbą od 1 do {MAX_QTY}.", "error")
            return redirect(url_for("cart"))

        update_item(session, product_id, variant_id, qty)
        flash("Zaktualizowano koszyk.", "success")
        return redirect(url_for("cart"))

    @app.get("/zamowienie")
    def order_redirect():
        # GET on the order endpoint just sends the visitor back to the
        # summary page — there is nothing to submit via GET.
        return redirect(url_for("cart"))

    @app.post("/zamowienie")
    def place_order():
        # Real pass: validate a non-empty cart, a known payment method, a known
        # delivery location and (for deliveries) an address; then show a mocked
        # confirmation and clear the cart. Invalid input never crashes — it
        # flashes a Polish message and returns to the summary page.
        payment_method = request.form.get("payment_method", "").strip()
        delivery_method = request.form.get("delivery_method", "").strip()
        address = request.form.get("address", "").strip()

        try:
            lines = cart_lines(session)
        except KeyError:
            # A stale/broken cart line can only exist if the catalog changed;
            # drop it instead of crashing the demo.
            clear_cart(session)
            flash(
                "Koszyk zawierał nieaktualne pozycje i został wyczyszczony.",
                "error",
            )
            return redirect(url_for("offer"))

        if not lines:
            flash(
                "Twój koszyk jest pusty. Dodaj produkty przed złożeniem zamówienia.",
                "error",
            )
            return redirect(url_for("cart"))

        if payment_method not in PAYMENT_METHODS:
            flash("Wybierz prawidłowy sposób płatności.", "error")
            return redirect(url_for("cart"))

        if delivery_method not in DELIVERY_METHODS:
            flash("Wybierz prawidłowe miejsce dostawy.", "error")
            return redirect(url_for("cart"))

        if delivery_method != PICKUP_DELIVERY and not address:
            flash(
                "Podaj adres dostawy (wymagany, gdy nie wybierasz odbioru osobistego).",
                "error",
            )
            return redirect(url_for("cart"))

        order_number = datetime.now().strftime("ZAM-%Y%m%d-%H%M%S")
        total = round(sum(line["line_total"] for line in lines), 2)
        order = {
            "number": order_number,
            "payment_label": PAYMENT_METHODS[payment_method],
            "delivery_label": DELIVERY_METHODS[delivery_method],
            "address": address if delivery_method != PICKUP_DELIVERY else None,
        }

        clear_cart(session)
        return render_template(
            "confirmation.html", lines=lines, total=total, order=order
        )

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(_error):
        return "Wystąpił błąd serwera.", 500

    return app
