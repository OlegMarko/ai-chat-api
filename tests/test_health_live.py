"""HTTP smoke: liveness does not touch Redis or Postgres."""

from starlette.testclient import TestClient

from app.main import create_app


def test_health_live_returns_status() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200

    assert response.json() == {"status": "live"}
