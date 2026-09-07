"""Flask application factory for the steel mock e-shop."""

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    session,
    url_for,
)

from stal.cart import cart_count
from stal.catalog import PRODUCTS
from stal.config import Config


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.context_processor
    def inject_cart_count():
        # Stub pass: cart_count() ignores the session and returns 0, but the
        # shared nav badge is already wired to the documented cart helper.
        return {"cart_count": cart_count(session)}

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/oferta")
    def offer():
        return render_template("shop.html", products=PRODUCTS)

    @app.post("/oferta/dodaj")
    def add_to_cart():
        # Stub: the route ignores the submitted form and flashes a fixed
        # message so the whole add-to-cart flow is clickable end-to-end.
        flash("Dodano do koszyka (wersja demonstracyjna).", "success")
        return redirect(url_for("offer"))

    @app.get("/koszyk")
    def cart():
        return render_template("cart.html")

    @app.post("/koszyk/aktualizuj")
    def update_cart():
        # Stub: the route ignores the submitted form and flashes a fixed
        # message so the whole update-cart flow is clickable end-to-end.
        flash("Koszyk zaktualizowany (wersja demonstracyjna).", "success")
        return redirect(url_for("cart"))

    @app.get("/zamowienie")
    def order_redirect():
        # Stub: GET on the order endpoint just sends the visitor back to the
        # summary page — there is nothing to submit via GET.
        return redirect(url_for("cart"))

    @app.post("/zamowienie")
    def place_order():
        # Stub: the route ignores the submitted form and renders a fixed
        # confirmation page so the whole checkout flow is clickable end-to-end.
        return render_template("confirmation.html")

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
