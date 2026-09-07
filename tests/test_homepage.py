"""Tests for M2 (real): homepage — full Polish copy.

These validate the real deliverable only:
- `templates/base.html` and `templates/index.html` exist and wire together,
- GET `/` renders a complete HTML document in Polish,
- the title is the real one (no leftover ``(stub)`` marker),
- the copy contains the company intro, the full assortment brainstorm
  (śruby, nakrętki, pręty, kątowniki, płaskowniki, rury; lengths 3 m / 6 m;
  quality variants such as S235JR / nierdzewna),
- the copy describes the current manual buying process and why buying online
  helps,
- there is a clear CTA to `/oferta` and a „wersja demonstracyjna" note.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "stal" / "templates"

ASSORTMENT = ("śruby", "nakrętki", "pręty", "kątowniki", "płaskowniki", "rury")


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
    assert "{% block title %}Stal — strona główna{% endblock %}" in index
    assert "{% block content %}" in index


# --- rendered route -------------------------------------------------------


def test_root_renders_the_homepage_template(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.mimetype == "text/html"

    html = resp.get_data(as_text=True)
    # A complete HTML document (base.html shell), not a bare fixed string.
    assert "<!doctype html>" in html
    assert '<html lang="pl">' in html
    assert "<body>" in html


def test_homepage_has_the_real_title_without_stub_marker(client):
    html = client.get("/").get_data(as_text=True)
    assert "<title>Stal — strona główna</title>" in html
    assert "(stub)" not in html
    assert "stub" not in html.lower()


def test_homepage_has_company_intro(client):
    html = client.get("/").get_data(as_text=True)
    assert "<h2>O nas</h2>" in html
    assert "hurtownią stali" in html


def test_homepage_summarizes_the_full_steel_assortment(client):
    html = client.get("/").get_data(as_text=True).lower()
    for item in ASSORTMENT:
        assert item in html, f"missing assortment term: {item}"


def test_homepage_mentions_stock_lengths_3m_and_6m(client):
    html = client.get("/").get_data(as_text=True)
    assert "3 m" in html
    assert "6 m" in html


def test_homepage_mentions_quality_variants(client):
    html = client.get("/").get_data(as_text=True)
    assert "S235JR" in html
    assert "nierdzewnej" in html


def test_homepage_describes_the_current_manual_buying_process(client):
    html = client.get("/").get_data(as_text=True)
    # The owner's phone → drive → window → printout → warehouse → cutting →
    # cash register → gate-check flow must be recognisable in the copy.
    for phrase in (
        "Dzwonisz do dostawcy",
        "Domu Stali",
        "ItalInox",
        "okienka",
        "karteczkę",
        "magazyn",
        "kasy",
        "ochroniarz",
    ):
        assert phrase in html, f"missing process phrase: {phrase}"


def test_homepage_explains_why_buying_online_helps(client):
    html = client.get("/").get_data(as_text=True)
    assert "Dlaczego warto kupować online" in html


def test_homepage_links_to_the_offer(client):
    html = client.get("/").get_data(as_text=True)
    assert 'href="/oferta"' in html
    assert "Przejdź do oferty" in html


def test_homepage_is_clearly_marked_as_a_demo(client):
    html = client.get("/").get_data(as_text=True).lower()
    assert "wersja demonstracyjna" in html
