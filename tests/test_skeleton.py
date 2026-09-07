"""Tests for M1 (real): app skeleton & runnable config.

These validate the real deliverable:
- a working Flask app factory,
- `/` renders the homepage and `/health` returns JSON ``{"status": "ok"}``,
- the 404 and 500 error handlers are registered and return safe Polish pages,
- the `app.py` entry point serves from the env-driven config,
- and the dependency / launcher files are present and wired correctly.
"""

import importlib
import os
from pathlib import Path

from flask import Flask

from stal import create_app

ROOT = Path(__file__).resolve().parent.parent


# --- app factory ---------------------------------------------------------


def test_create_app_returns_flask_app(app):
    assert isinstance(app, Flask)


def test_root_returns_homepage(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.mimetype == "text/html"
    text = resp.get_data(as_text=True)
    assert "Stal" in text
    # The homepage is now the real M2 copy in this pass.
    assert "O nas" in text
    assert "(stub)" not in text


def test_health_returns_json_status_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    assert resp.get_json() == {"status": "ok"}


def test_unknown_route_returns_404_and_polish_template(client):
    resp = client.get("/taka-strona-nie-istnieje")
    assert resp.status_code == 404
    assert resp.mimetype == "text/html"
    text = resp.get_data(as_text=True)
    assert "Nie znaleziono strony" in text


def test_internal_error_returns_safe_polish_message():
    app = create_app()

    @app.route("/_boom")
    def _boom():
        raise RuntimeError("boom")

    app.testing = False
    client = app.test_client()
    resp = client.get("/_boom")
    assert resp.status_code == 500
    assert resp.get_data(as_text=True) == "Wystąpił błąd serwera."


def test_error_handlers_are_registered(app):
    handlers = app.error_handler_spec[None]
    assert 404 in handlers
    assert 500 in handlers


# --- entry point ---------------------------------------------------------


def test_app_py_exposes_a_flask_app():
    module = importlib.import_module("app")
    assert isinstance(module.app, Flask)
    rules = {rule.rule for rule in module.app.url_map.iter_rules()}
    assert "/" in rules
    assert "/health" in rules


def test_app_py_guard_prevents_auto_run_on_import():
    importlib.import_module("app")  # must not start the dev server
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in source
    assert "app.run(" in source


def test_app_py_serves_from_config():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'host=app.config["HOST"]' in source
    assert 'port=app.config["PORT"]' in source
    assert 'debug=app.config["FLASK_DEBUG"]' in source


# --- dependency & launcher files ----------------------------------------


def test_runtime_requirements_list_flask():
    content = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "Flask" in content


def test_dev_requirements_include_runtime_and_pytest():
    content = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    assert "-r requirements.txt" in content
    assert "pytest" in content


def test_run_scripts_create_venv_install_and_run():
    sh = (ROOT / "run.sh").read_text(encoding="utf-8")
    bat = (ROOT / "run.bat").read_text(encoding="utf-8")
    for content in (sh, bat):
        assert "venv" in content
        assert "pip install -r requirements.txt" in content
        assert "python app.py" in content


def test_run_sh_is_executable():
    assert os.access(ROOT / "run.sh", os.X_OK)
