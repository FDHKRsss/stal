"""Tests for the M1/M2 stub environment handling and doc polish items.

These validate the *current* stub deliverables precisely:
- the stub config is static (it must NOT read the process environment or a
  `.env` file; env-driven config arrives in the real pass),
- `.env.example` tells the truth about that stub behavior,
- `PLAN.md` marks exactly `M1 -- stub` and `M2 -- stub` done, leaves every
  other milestone unchecked, and points the next action at `M3 -- stub`,
- `ARCHITECTURE.md`'s "What's in code" section describes the *implemented*
  state (M1 + M2 stubs), and its implemented / not-yet lists match the disk.
"""

from pathlib import Path

from stal import create_app

ROOT = Path(__file__).resolve().parent.parent


# --- stub environment behavior (the ground truth the docs must match) -----


def test_stub_config_ignores_environment_variables(monkeypatch):
    """The stub pass is static: setting env vars must not leak into config."""
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "9999")
    monkeypatch.setenv("SECRET_KEY", "inny-klucz")
    monkeypatch.setenv("FLASK_DEBUG", "1")

    app = create_app()
    assert app.config["HOST"] == "127.0.0.1"
    assert app.config["PORT"] == 5000
    assert app.config["SECRET_KEY"] == "dev-only-stub-key"
    assert app.config["FLASK_DEBUG"] is False


def test_stub_has_no_dotenv_dependency():
    """The stub must not pull in a `.env` loader; auto-load arrives later."""
    runtime = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "dotenv" not in runtime.lower()


def test_stub_config_module_does_not_read_environment():
    """`stal/config.py` is static defaults only in the stub pass."""
    source = (ROOT / "stal" / "config.py").read_text(encoding="utf-8")
    assert "os.environ" not in source
    assert "getenv" not in source
    assert "load_dotenv" not in source


# --- `.env.example` accuracy ---------------------------------------------


def test_env_example_explicitly_disclaims_that_the_stub_autoloads_env():
    content = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "NIE wczytuje pliku .env automatycznie" in content


def test_env_example_says_stub_uses_static_config_defaults():
    content = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "statycznych" in content
    assert "stal/config.py" in content


def test_env_example_says_setting_env_vars_does_not_change_stub_yet():
    content = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "nie zmienia jeszcze działania aplikacji" in content


def test_env_example_says_env_config_arrives_in_real_pass():
    content = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "real pass" in content


def test_env_example_does_not_instruct_setting_or_exporting_env_vars():
    """The stub ignores env vars, so the file must not tell users to `set` /
    `export` them as if that changed the running stub app."""
    content = (ROOT / ".env.example").read_text(encoding="utf-8")
    lower = content.lower()
    # The exact instruction the old file used (must be gone) …
    assert "ustaw zmienne bezpośrednio w środowisku" not in content
    # … and no shell-specific set/export instructions either.
    for token in ("export ", "set ", "setx ", "$env:"):
        assert token not in lower


# --- `PLAN.md` milestone state -------------------------------------------


def test_plan_marks_m1_and_m2_stub_done():
    content = (ROOT / "docs" / "PLAN.md").read_text(encoding="utf-8")
    lines = content.splitlines()
    checked = [ln.strip() for ln in lines if ln.strip().startswith("- [x]")]
    assert checked == ["- [x] M1 -- stub", "- [x] M2 -- stub"]

    # Cosmetic count fix (critic): the M2 acceptance note must say 35 tests
    # green (not the stale 30), while the historical M1 note stays at 23.
    assert "**M2 -- stub accepted** — 35 tests green" in content
    assert "**M2 -- stub accepted** — 30 tests green" not in content
    assert "**M1 -- stub accepted** — 23 tests green" in content
    assert "30 tests green" not in content


def test_plan_m1_real_and_all_other_milestones_still_unchecked():
    content = (ROOT / "docs" / "PLAN.md").read_text(encoding="utf-8")
    assert "- [ ] M1 -- real" in content
    for n in range(3, 10):
        assert f"- [ ] M{n} -- stub" in content
        assert f"- [ ] M{n} -- real" in content


def test_plan_next_action_points_to_m3_stub():
    content = (ROOT / "docs" / "PLAN.md").read_text(encoding="utf-8")
    assert "Next action: implement **M3 -- stub**" in content


# --- `ARCHITECTURE.md` "What's in code" accuracy --------------------------


def _whats_in_code_section():
    arch = (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
    return arch.split("## What's in code", 1)[1]


def test_architecture_records_m1_and_m2_stub_as_implemented():
    section = _whats_in_code_section()
    assert "Implemented so far (Pass 1):" in section
    assert "`M1 -- stub`" in section
    assert "`M2 -- stub`" in section
    # The routes are described as rendering the real template (not fixed text).
    assert "`/` renders `index.html`" in section
    assert "`/health` returns" in section
    # Cosmetic count fix (critic): the test bullet must say 35 passing, not 30.
    assert "**35 passing**" in section
    assert "**30 passing**" not in section


def test_architecture_lists_implemented_files_that_exist_on_disk():
    section = _whats_in_code_section()
    implemented = {
        "app.py": "app.py",
        "stal/__init__.py": "stal/__init__.py",
        "stal/config.py": "stal/config.py",
        "stal/templates/base.html": "stal/templates/base.html",
        "stal/templates/index.html": "stal/templates/index.html",
        "requirements.txt": "requirements.txt",
        "requirements-dev.txt": "requirements-dev.txt",
        "pytest.ini": "pytest.ini",
        ".env.example": ".env.example",
        "run.bat": "run.bat",
        "run.sh": "run.sh",
    }
    for name, rel in implemented.items():
        assert name in section, f"{name} not listed under 'What's in code'"
        assert (ROOT / rel).is_file(), f"{rel} listed as implemented but missing"


def test_architecture_marks_unimplemented_files_as_not_yet_existing():
    section = _whats_in_code_section()
    assert "Not implemented yet" in section
    not_yet = section.split("Not implemented yet", 1)[1]
    unimplemented = {
        "catalog.py": "stal/catalog.py",
        "cart.py": "stal/cart.py",
        "routes.py": "stal/routes.py",
        "static/": "stal/static",
        "shop.html": "stal/templates/shop.html",
        "cart.html": "stal/templates/cart.html",
        "confirmation.html": "stal/templates/confirmation.html",
        "404.html": "stal/templates/404.html",
        "test_cart.py": "tests/test_cart.py",
        "test_routes.py": "tests/test_routes.py",
    }
    for name, rel in unimplemented.items():
        assert name in not_yet, f"{name} not listed under 'Not implemented yet'"
        assert not (ROOT / rel).exists(), f"{rel} listed as not-yet but exists on disk"


def test_architecture_has_m2_stub_acceptance_note():
    arch = (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "accepted **M2 -- stub**" in arch
    # Cosmetic count fix (critic): M2 review note says 35 tests green (not 30),
    # the historical M1 note keeps its 23, and no stale 30 strings remain.
    assert "accepted **M2 -- stub** (35 tests green)" in arch
    assert "accepted **M2 -- stub** (30 tests green)" not in arch
    assert "accepted **M1 -- stub** (23 tests green)" in arch
    assert "30 tests green" not in arch
    assert "30 passing" not in arch
