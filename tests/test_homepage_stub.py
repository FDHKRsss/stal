"""Tests for M2 (stub): homepage — description + brainstorm.

These validate the current stub deliverable only:
- `templates/base.html` and `templates/index.html` exist and wire together,
- `index.html` extends `base.html` and overrides the title block,
- GET `/` renders that template (an HTML document, not a fixed string) and
  summarizes the steel-trade topic in Polish, clearly marked as a demo/stub.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "stal" / "templates"


# --- template files -------------------------------------------------------


def test_homepage_template_files_exist():
    assert (TEMPLATES / "base.html").is_file()
    assert (TEMPLATES / "index.html").is_file()


def test_base_template_is_polish_layout_with_blocks():
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert '<html lang="pl">' in base
    assert "{% block title %}" in base
    assert "{% block content %}" in base


def test_index_template_extends_base_and_fills_content():
    index = (TEMPLATES / "index.html").read_text(encoding="utf-8")
    assert '{% extends "base.html" %}' in index
    assert "{% block content %}" in index


# --- rendered route -------------------------------------------------------


def test_root_renders_the_homepage_template(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.mimetype == "text/html"

    html = resp.get_data(as_text=True)
    # A rendered HTML document (base.html shell), not a bare fixed string.
    assert "<!doctype html>" in html
    assert '<html lang="pl">' in html
    assert "<body>" in html


def test_homepage_overrides_the_title_block(client):
    html = client.get("/").get_data(as_text=True)
    assert "<title>Stal — strona główna (stub)</title>" in html


def test_homepage_summarizes_the_steel_assortment(client):
    html = client.get("/").get_data(as_text=True)
    assert "<h1>Stal</h1>" in html
    for item in ("śruby", "nakrętki", "pręty", "kątowniki", "płaskowniki", "rury"):
        assert item in html


def test_homepage_is_clearly_marked_as_a_mock_stub(client):
    html = client.get("/").get_data(as_text=True).lower()
    assert "stub" in html
    assert "demonstracyjna" in html
