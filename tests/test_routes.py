"""Tests for the route flow (M9).

Real pass starts with M1: `/health` now returns JSON ``{"status": "ok"}``.
The full end-to-end flow (`/` -> `/oferta` -> add -> `/koszyk` -> update ->
`/zamowienie`) and the validation / error cases arrive with the later real
milestones and will be tested here.
"""

from flask import Flask

from stal import create_app


def test_app_factory_and_health_smoke():
    """Smoke test: the factory builds an app and `/health` answers 200 JSON."""
    app = create_app()
    assert isinstance(app, Flask)

    client = app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    assert resp.get_json() == {"status": "ok"}
