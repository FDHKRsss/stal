"""Tests for the M1 stub's environment handling and doc polish items.

These validate the *current* stub deliverable precisely:
- the stub config is static (it must NOT read the process environment or a
  `.env` file; env-driven config arrives in the real pass),
- `.env.example` tells the truth about that stub behavior,
- `PLAN.md` marks exactly `M1 -- stub` done and leaves every other milestone
  unchecked.
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


def test_plan_marks_only_m1_stub_done():
    lines = (ROOT / "docs" / "PLAN.md").read_text(encoding="utf-8").splitlines()
    checked = [ln.strip() for ln in lines if ln.strip().startswith("- [x]")]
    assert checked == ["- [x] M1 -- stub"]


def test_plan_m1_real_and_all_other_milestones_still_unchecked():
    content = (ROOT / "docs" / "PLAN.md").read_text(encoding="utf-8")
    assert "- [ ] M1 -- real" in content
    for n in range(2, 10):
        assert f"- [ ] M{n} -- stub" in content
        assert f"- [ ] M{n} -- real" in content
