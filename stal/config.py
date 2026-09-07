"""Application configuration (real pass).

``HOST`` / ``PORT`` / ``SECRET_KEY`` / ``FLASK_DEBUG`` are read from
``os.environ`` with sane defaults, so the app runs with no setup on Windows and
Ubuntu. The app never auto-loads a ``.env`` file; ``.env.example`` is
documentation only.
"""

import os


def _env_bool(name, default):
    """Read a boolean env var, accepting 1/true/yes/on (case-insensitive)."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name, default):
    """Read an integer env var, falling back to ``default`` on bad input."""
    raw = os.environ.get(name)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


class Config:
    """Environment-driven configuration with sane defaults."""

    HOST = os.environ.get("HOST") or "127.0.0.1"
    PORT = _env_int("PORT", 5000)
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-only-secret-key"
    FLASK_DEBUG = _env_bool("FLASK_DEBUG", False)
