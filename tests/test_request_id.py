"""Correlation ID middleware echoes or generates `x-request-id`."""

from starlette.testclient import TestClient

from app.main import create_app


def test_request_id_echoed_when_provided() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/health/live", headers={"x-request-id": "trace-unit-7"})

    assert response.status_code == 200

    assert response.headers.get("x-request-id") == "trace-unit-7"


def test_request_id_generated_when_absent() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200

    assert "x-request-id" in response.headers

    assert len(response.headers["x-request-id"]) >= 8
