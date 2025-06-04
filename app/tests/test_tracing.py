from __future__ import annotations

import io

import pytest
from PIL import Image

from app.core.tracing import apply_fill, raster_to_svg


def _sample_image() -> bytes:
    img = Image.new("RGB", (2, 2), "white")
    img.putpixel((0, 0), (0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_svg_generation() -> None:
    svg = raster_to_svg(_sample_image())
    assert "<svg" in svg and "<path" in svg


def test_apply_fill() -> None:
    svg = raster_to_svg(_sample_image())
    red = apply_fill(svg, "#ff0000")
    assert "#ff0000" in red


def test_invalid_image() -> None:
    with pytest.raises(ValueError):
        raster_to_svg(b"bad")


def test_threshold_effect() -> None:
    img = Image.new("L", (2, 2), 128)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    empty = raster_to_svg(buf.getvalue(), threshold=255)
    filled = raster_to_svg(buf.getvalue(), threshold=0)
    assert 'd=""' in empty
    assert 'd=""' not in filled
