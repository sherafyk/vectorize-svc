from __future__ import annotations

import io
import re
from xml.etree import ElementTree as ET

import pytest
from PIL import Image

from app.core.tracing import apply_fill, raster_to_svg


def _sample_image(fmt: str = "PNG") -> bytes:
    img = Image.new("RGB", (2, 2), "white")
    img.putpixel((0, 0), (0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


@pytest.mark.parametrize("fmt", ["PNG", "JPEG", "WEBP"])
def test_svg_generation(fmt: str) -> None:
    svg = raster_to_svg(_sample_image(fmt))
    assert "<svg" in svg and "<path" in svg
    assert 'width="250"' in svg and 'height="250"' in svg


@pytest.mark.parametrize("fmt", ["PNG", "JPEG", "WEBP"])
def test_apply_fill(fmt: str) -> None:
    svg = raster_to_svg(_sample_image(fmt))
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


def test_custom_size() -> None:
    svg = raster_to_svg(_sample_image(), size=100)
    assert 'width="100"' in svg and 'height="100"' in svg


def test_numeric_rounding() -> None:
    """Ensure numeric values are rounded to at most one decimal place."""
    svg = raster_to_svg(_sample_image())
    tree = ET.fromstring(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    path_d = tree.find(".//svg:path", ns).attrib.get("d", "")
    numbers = re.findall(r"-?\d+(?:\.\d+)?", path_d)
    transform = tree.find('.//svg:g[@transform]', ns).attrib.get('transform', '')
    numbers += re.findall(r"-?\d+(?:\.\d+)?", transform)
    for num in numbers:
        if '.' in num:
            assert len(num.split('.')[1]) <= 1
