"""Tests for the real (Pass 2) environment-driven config and doc state.

The M1 real deliverable makes ``stal/config.py`` read ``HOST`` / ``PORT`` /
``SECRET_KEY`` / ``FLASK_DEBUG`` from ``os.environ`` with sane defaults, with
no ``.env`` auto-loading (no python-dotenv). This file validates that behavior
and its edge cases, and checks that ``PLAN.md`` / ``ARCHITECTURE.md`` keep up
with the implemented state.
"""

import importlib
import os
from pathlib import Path

import pytest

import stal
import stal.config as config_module

ROOT = Path(__file__).resolve().parent.parent
_CONFIG_ENV = ("HOST", "PORT", "SECRET_KEY", "FLASK_DEBUG")


# --- reload helpers (Config reads the environment at import time) ---------


def _reload_config_and_app():
    importlib.reload(config_module)
    importlib.reload(stal)


def _isolate_env(**overrides):
    """Clear the four config env vars, apply ``overrides``, return saved state."""
    saved = {key: os.environ.get(key) for key in _CONFIG_ENV}
    for key in _CONFIG_ENV:
        os.environ.pop(key, None)
    os.environ.update(overrides)
    return saved


def _restore_env(saved):
    for key in _CONFIG_ENV:
        os.environ.pop(key, None)
    for key, value in saved.items():
        if value is not None:
            os.environ[key] = value


# --- sane defaults --------------------------------------------------------


def test_config_defaults_are_sane():
    saved = _isolate_env()
    try:
        _reload_config_and_app()
        config = config_module.Config
        assert config.HOST == "127.0.0.1"
        assert config.PORT == 5000
        assert isinstance(config.PORT, int)
        assert config.FLASK_DEBUG is False
        assert config.SECRET_KEY == "dev-only-secret-key"
        assert config.SECRET_KEY  # non-empty
    finally:
        _restore_env(saved)
        _reload_config_and_app()


# --- env overrides --------------------------------------------------------


def test_config_reads_env_overrides():
    saved = _isolate_env(
        HOST="0.0.0.0", PORT="9999", SECRET_KEY="tajny", FLASK_DEBUG="1"
    )
    try:
        _reload_config_and_app()
        config = config_module.Config
        assert config.HOST == "0.0.0.0"
        assert config.PORT == 9999
        assert config.SECRET_KEY == "tajny"
        assert config.FLASK_DEBUG is True
    finally:
        _restore_env(saved)
        _reload_config_and_app()


def test_empty_string_env_vars_fall_back_to_defaults():
    saved = _isolate_env(HOST="", PORT="", SECRET_KEY="", FLASK_DEBUG="")
    try:
        _reload_config_and_app()
        config = config_module.Config
        assert config.HOST == "127.0.0.1"
        assert config.PORT == 5000
        assert config.SECRET_KEY == "dev-only-secret-key"
        assert config.FLASK_DEBUG is False
    finally:
        _restore_env(saved)
        _reload_config_and_app()


def test_create_app_uses_env_driven_config():
    saved = _isolate_env(
        HOST="0.0.0.0", PORT="9999", SECRET_KEY="tajny", FLASK_DEBUG="1"
    )
    try:
        _reload_config_and_app()
        app = stal.create_app()
        assert app.config["HOST"] == "0.0.0.0"
        assert app.config["PORT"] == 9999
        assert app.config["SECRET_KEY"] == "tajny"
        assert app.config["FLASK_DEBUG"] is True
    finally:
        _restore_env(saved)
        _reload_config_and_app()


# --- robust parsing of PORT / FLASK_DEBUG ---------------------------------


def test_env_int_parses_valid_port(monkeypatch):
    monkeypatch.setenv("PORT", "9999")
    assert config_module._env_int("PORT", 5000) == 9999


def test_env_int_falls_back_on_invalid_or_empty(monkeypatch):
    monkeypatch.setenv("PORT", "abc")
    assert config_module._env_int("PORT", 5000) == 5000
    monkeypatch.setenv("PORT", "")
    assert config_module._env_int("PORT", 5000) == 5000


def test_env_bool_accepts_truthy_values(monkeypatch):
    for value in ("1", "true", "TRUE", "yes", "on", "On"):
        monkeypatch.setenv("FLASK_DEBUG", value)
        assert config_module._env_bool("FLASK_DEBUG", False) is True


def test_env_bool_treats_other_values_as_false(monkeypatch):
    for value in ("0", "false", "no", "off", ""):
        monkeypatch.setenv("FLASK_DEBUG", value)
        assert config_module._env_bool("FLASK_DEBUG", True) is False


# --- no `.env` auto-loading ----------------------------------------------


def test_config_module_reads_only_os_environ():
    source = (ROOT / "stal" / "config.py").read_text(encoding="utf-8")
    assert "os.environ" in source
    assert "load_dotenv" not in source
    assert "dotenv" not in source.lower()


def test_no_dotenv_dependency():
    runtime = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    dev = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    for content in (runtime, dev):
        assert "dotenv" not in content.lower()


# --- `.env.example` truthfulness ------------------------------------------


def test_env_example_disclaims_auto_loading():
    content = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "NIE wczytuje tego pliku automatycznie" in content
    assert "python-dotenv" in content
    assert "os.environ" in content


def test_env_example_shows_how_to_set_vars_per_platform():
    content = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "export HOST=" in content
    assert "set HOST=" in content
    assert "$env:HOST=" in content


# --- PLAN.md / ARCHITECTURE.md doc state ----------------------------------


def _plan_text():
    return (ROOT / "docs" / "PLAN.md").read_text(encoding="utf-8")


def _arch_text():
    return (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")


def test_plan_still_marks_all_stubs_done():
    content = _plan_text()
    for n in range(1, 10):
        assert f"- [x] M{n} -- stub" in content


def test_plan_marks_m1_real_done():
    assert "- [x] M1 -- real" in _plan_text()


def test_plan_other_real_steps_still_unchecked():
    content = _plan_text()
    for n in range(2, 10):
        assert f"- [ ] M{n} -- real" in content


def test_plan_next_action_points_to_m2_real():
    assert "Next action: implement **M2 -- real**" in _plan_text()


def test_plan_has_m1_real_acceptance_note():
    assert "M1 -- real accepted" in _plan_text()


def test_architecture_config_described_as_env_driven():
    arch = _arch_text()
    section = arch.split("## What's in code", 1)[1]
    assert "os.environ" in section
    assert "env-driven" in section


def test_architecture_404_is_implemented_and_routes_still_missing():
    arch = _arch_text()
    section = arch.split("## What's in code", 1)[1]
    assert "Not implemented yet" in section
    not_yet = section.split("Not implemented yet", 1)[1]
    assert "404.html" not in not_yet
    assert (ROOT / "stal" / "templates" / "404.html").is_file()
    assert "routes.py" in not_yet
    assert not (ROOT / "stal" / "routes.py").exists()


def test_architecture_has_m1_real_acceptance_note():
    assert "accepted **M1 -- real**" in _arch_text()
