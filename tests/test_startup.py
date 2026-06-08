from src.main import app


def test_app_startup_configuration() -> None:
    assert app.title == "PennyServ API"
    assert app.openapi_url == "/openapi.json"
