import io
from unittest.mock import patch

import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app


def _img_bytes(fmt: str = "PNG") -> bytes:
    img = Image.new("RGB", (2, 2), "white")
    img.putpixel((0, 0), (0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


class _Resp:
    def __init__(self, fmt: str = "PNG"):
        self.fmt = fmt

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def read(self) -> bytes:
        return _img_bytes(self.fmt)


@pytest.mark.parametrize(
    "fmt,ext",
    [
        ("PNG", "png"),
        ("JPEG", "jpg"),
        ("WEBP", "webp"),
    ],
)
def test_vectorize_image_url(fmt: str, ext: str) -> None:
    client = TestClient(app)
    with patch("urllib.request.urlopen", return_value=_Resp(fmt)):
        resp = client.post(f"/vectorize?image_url=http://example.com/img.{ext}")
    assert resp.status_code == 200
    body = resp.json()["svg"]
    assert body.startswith("<svg") and body.endswith("</svg>")
    assert "\\" not in body


def test_vectorize_custom_size() -> None:
    client = TestClient(app)
    with patch("urllib.request.urlopen", return_value=_Resp("PNG")):
        resp = client.post("/vectorize?image_url=http://example.com/img.png&size=100")
    assert resp.status_code == 200
    body = resp.json()["svg"]
    assert 'width="100"' in body and 'height="100"' in body


@pytest.mark.parametrize(
    "fmt,ext",
    [
        ("PNG", "png"),
        ("JPEG", "jpg"),
        ("WEBP", "webp"),
    ],
)
def test_vectorize_image_url_get(fmt: str, ext: str) -> None:
    client = TestClient(app)
    with patch("urllib.request.urlopen", return_value=_Resp(fmt)):
        resp = client.get(f"/vectorize?image_url=http://example.com/img.{ext}")
    assert resp.status_code == 200
    body = resp.json()["svg"]
    assert body.startswith("<svg") and body.endswith("</svg>")
    assert "\\" not in body


@pytest.mark.parametrize(
    "fmt,mime,ext",
    [
        ("PNG", "image/png", "png"),
        ("JPEG", "image/jpeg", "jpg"),
        ("WEBP", "image/webp", "webp"),
    ],
)
def test_auth_header(fmt: str, mime: str, ext: str) -> None:
    with patch("app.main.API_TOKEN", "secret"):
        client = TestClient(app)
        resp = client.post(
            "/vectorize",
            headers={"Authorization": "Bearer secret"},
            files={"image": (f"img.{ext}", _img_bytes(fmt), mime)},
        )
        assert resp.status_code == 200


@pytest.mark.parametrize(
    "fmt,mime,ext",
    [
        ("PNG", "image/png", "png"),
        ("JPEG", "image/jpeg", "jpg"),
        ("WEBP", "image/webp", "webp"),
    ],
)
def test_auth_query_param(fmt: str, mime: str, ext: str) -> None:
    with patch("app.main.API_TOKEN", "secret"):
        client = TestClient(app)
        resp = client.post(
            "/vectorize?token=secret",
            files={"image": (f"img.{ext}", _img_bytes(fmt), mime)},
        )
        assert resp.status_code == 200


@pytest.mark.parametrize(
    "fmt,ext",
    [
        ("PNG", "png"),
        ("JPEG", "jpg"),
        ("WEBP", "webp"),
    ],
)
def test_auth_query_param_get(fmt: str, ext: str) -> None:
    """Ensure token works when using GET /vectorize."""
    with patch("app.main.API_TOKEN", "secret"):
        client = TestClient(app)
        with patch("urllib.request.urlopen", return_value=_Resp(fmt)):
            resp = client.get(
                f"/vectorize?image_url=http://example.com/img.{ext}&token=secret"
            )
        assert resp.status_code == 200


def test_additional_params() -> None:
    client = TestClient(app)
    with patch("urllib.request.urlopen", return_value=_Resp("PNG")):
        resp = client.post(
            "/vectorize?image_url=http://example.com/img.png&opticurve=false&opttolerance=0.5&stroke=%23000000&stroke_width=2&invert=true&passes=2&autocrop=true",
        )
    assert resp.status_code == 200
    assert 'stroke="#000000"' in resp.json()["svg"]
