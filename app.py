"""Entry point: build the app and serve it."""

from stal import create_app
from stal.config import Config

app = create_app()

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.FLASK_DEBUG)
