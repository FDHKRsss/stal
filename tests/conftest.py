"""Shared pytest fixtures for the steel mock e-shop."""

import pytest

from stal import create_app


@pytest.fixture
def app():
    """A fresh Flask application built by the factory."""
    return create_app()


@pytest.fixture
def client(app):
    """Flask test client bound to the factory app (no port bound)."""
    return app.test_client()
