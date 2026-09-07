"""Flask application factory for the steel mock e-shop."""

from flask import Flask

from stal.config import Config


def create_app():
    """Create and configure the Flask application (stub pass)."""
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.get("/")
    def index():
        return "Stal — wersja demonstracyjna (stub)"

    @app.get("/health")
    def health():
        return "ok"

    return app
