from fastapi.testclient import TestClient

from collabpilot.bootstrap import create_application, get_settings
from collabpilot.interfaces.api import create_api


def test_health() -> None:
    get_settings.cache_clear()
    create_application.cache_clear()
    with TestClient(create_api()) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_with_mock() -> None:
    get_settings.cache_clear()
    create_application.cache_clear()
    with TestClient(create_api()) as client:
        response = client.post(
            "/v1/chat",
            json={"message": "你好", "provider": "mock"},
        )
    assert response.status_code == 200
    assert response.json()["provider"] == "mock"


def test_course_ppt_origin_is_allowed() -> None:
    get_settings.cache_clear()
    create_application.cache_clear()
    with TestClient(create_api()) as client:
        response = client.options(
            "/v1/chat",
            headers={
                "Origin": "http://127.0.0.1:8001",
                "Access-Control-Request-Method": "POST",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:8001"


def test_stream_chat_with_mock() -> None:
    get_settings.cache_clear()
    create_application.cache_clear()
    with TestClient(create_api()) as client:
        with client.stream(
            "POST",
            "/v1/chat/stream",
            json={"message": "你好", "provider": "mock"},
        ) as response:
            body = "".join(response.iter_text())
    assert response.status_code == 200
    assert '"type": "delta"' in body
    assert '"type": "done"' in body
    assert '"session_id"' in body
