import io
from unittest.mock import patch
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app


def _img_bytes() -> bytes:
    img = Image.new("RGB", (2, 2), "white")
    img.putpixel((0, 0), (0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class _Resp:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def read(self) -> bytes:
        return _img_bytes()


def test_vectorize_image_url() -> None:
    client = TestClient(app)
    with patch("urllib.request.urlopen", return_value=_Resp()):
        resp = client.post("/vectorize?image_url=http://example.com/img.png")
    assert resp.status_code == 200
    assert "<svg" in resp.json()["svg"]


def test_vectorize_image_url_get() -> None:
    client = TestClient(app)
    with patch("urllib.request.urlopen", return_value=_Resp()):
        resp = client.get("/vectorize?image_url=http://example.com/img.png")
    assert resp.status_code == 200
    assert "<svg" in resp.json()["svg"]


def test_auth_header() -> None:
    with patch("app.main.API_TOKEN", "secret"):
        client = TestClient(app)
        resp = client.post(
            "/vectorize",
            headers={"Authorization": "Bearer secret"},
            files={"image": ("img.png", _img_bytes(), "image/png")},
        )
        assert resp.status_code == 200


def test_auth_query_param() -> None:
    with patch("app.main.API_TOKEN", "secret"):
        client = TestClient(app)
        resp = client.post(
            "/vectorize?token=secret",
            files={"image": ("img.png", _img_bytes(), "image/png")},
        )
        assert resp.status_code == 200
