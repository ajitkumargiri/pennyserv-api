from fastapi.testclient import TestClient


def test_health_live(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "pennyserv-api"
    assert "version" in payload


def test_health_ready(client: TestClient) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "pennyserv-api"
    assert isinstance(payload["components"], list)


def test_openapi_loads(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "PennyServ API"
