"""FastAPI validation on request bodies (no external services on /health)."""

from starlette.testclient import TestClient

from app.main import create_app


def test_chat_rejects_empty_message() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post("/chat", json={"message": "", "session_id": "s1"})

    assert response.status_code == 422


def test_rag_rejects_empty_question() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post("/rag", json={"question": "", "session_id": "s1"})

    assert response.status_code == 422


def test_ingest_rejects_empty_documents_list() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post("/ingest", json={"documents": []})

    assert response.status_code == 422
