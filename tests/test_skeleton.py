"""Tests for M1 (stub): app skeleton & runnable config.

These validate the current stub deliverable only:
- a working Flask app factory,
- the two stub routes `/` and `/health` returning fixed text,
- sane static config defaults,
- the `app.py` entry point wiring,
- and the dependency / launcher / env documentation files.
"""

import importlib
import os
from pathlib import Path

from flask import Flask

from stal.config import Config

ROOT = Path(__file__).resolve().parent.parent


# --- app factory ---------------------------------------------------------


def test_create_app_returns_flask_app(app):
    assert isinstance(app, Flask)


def test_root_returns_stub_text(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.mimetype == "text/html"
    text = resp.get_data(as_text=True)
    assert "Stal" in text
    assert "stub" in text.lower()


def test_health_returns_fixed_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == "ok"


def test_unknown_route_returns_404(client):
    resp = client.get("/taka-strona-nie-istnieje")
    assert resp.status_code == 404


# --- configuration defaults ---------------------------------------------


def test_config_defaults_are_sane():
    assert Config.HOST == "127.0.0.1"
    assert Config.PORT == 5000
    assert isinstance(Config.PORT, int)
    assert Config.FLASK_DEBUG is False
    assert isinstance(Config.SECRET_KEY, str)
    assert Config.SECRET_KEY  # non-empty


def test_app_config_is_loaded_from_config_object(app):
    assert app.config["HOST"] == "127.0.0.1"
    assert app.config["PORT"] == 5000
    assert app.config["FLASK_DEBUG"] is False
    assert app.config["SECRET_KEY"] == Config.SECRET_KEY


# --- entry point ---------------------------------------------------------


def test_app_py_exposes_a_flask_app():
    module = importlib.import_module("app")
    assert isinstance(module.app, Flask)
    # The entry point must serve the two stub routes too.
    rules = {rule.rule for rule in module.app.url_map.iter_rules()}
    assert "/" in rules
    assert "/health" in rules


def test_app_py_guard_prevents_auto_run_on_import():
    importlib.import_module("app")  # must not start the dev server
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in source
    assert "app.run(" in source


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


def test_env_example_documents_config_vars():
    content = (ROOT / ".env.example").read_text(encoding="utf-8")
    for var in ("HOST", "PORT", "SECRET_KEY", "FLASK_DEBUG"):
        assert var in content
