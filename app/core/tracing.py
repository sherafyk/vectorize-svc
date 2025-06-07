"""Core tracing utilities.

Example:
    >>> from vectorize_svc.core.tracing import raster_to_svg, apply_fill
    >>> with open('image.png', 'rb') as f:
    ...     svg = raster_to_svg(f.read())
    >>> colored = apply_fill(svg, '#ff0000')
"""

from __future__ import annotations

import io
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image, ImageFilter
import potrace

ET.register_namespace("", "http://www.w3.org/2000/svg")


def _fmt(num: float) -> str:
    """Format numeric values for the SVG output."""
    rounded = round(num)
    if abs(num - rounded) < 1e-6:
        return str(int(rounded))
    return f"{round(num, 1):.1f}".rstrip("0").rstrip(".")


TURNPOLICIES: dict[str, int] = {
    "black": potrace.TURNPOLICY_BLACK,
    "white": potrace.TURNPOLICY_WHITE,
    "left": potrace.TURNPOLICY_LEFT,
    "right": potrace.TURNPOLICY_RIGHT,
    "minority": potrace.TURNPOLICY_MINORITY,
    "majority": potrace.TURNPOLICY_MAJORITY,
    "random": potrace.TURNPOLICY_RANDOM,
}


def raster_to_svg(
    data: bytes,
    threshold: int = 128,
    turnpolicy: str = "minority",
    alphamax: float = 1.0,
    turdsize: int = 2,
    size: int = 250,
    opticurve: bool = True,
    opttolerance: float = 0.2,
    background: str | None = None,
    invert: bool = False,
    passes: int = 1,
    autocrop: bool = False,
) -> str:
    """Convert raster image bytes to a normalized SVG string.

    The resulting SVG is always a square with the given ``size``. The original
    tracing coordinates are scaled and centered to fit inside this square while
    preserving aspect ratio.
    """
    try:
        image = Image.open(io.BytesIO(data))
    except Exception as exc:  # pragma: no cover - invalid image
        raise ValueError("Invalid image") from exc

    if background:
        bg = Image.new("RGBA", image.size, background)
        img_rgba = image.convert("RGBA")
        mask = img_rgba.split()[3] if "A" in img_rgba.getbands() else None
        bg.paste(img_rgba, mask=mask)
        image = bg

    if autocrop:
        if "A" in image.getbands():
            bbox = image.getchannel("A").getbbox()
        else:
            bbox = image.getbbox()
        if bbox:
            image = image.crop(bbox)

    gray = image.convert("L")
    for _ in range(max(0, passes - 1)):
        gray = gray.filter(ImageFilter.SMOOTH)

    width, height = gray.size
    arr = np.array(gray)
    if invert:
        arr = 255 - arr
    bitmap = potrace.Bitmap(arr > threshold)
    path = bitmap.trace(
        turdsize=turdsize,
        turnpolicy=TURNPOLICIES.get(turnpolicy, potrace.TURNPOLICY_MINORITY),
        alphamax=alphamax,
        opticurve=1 if opticurve else 0,
        opttolerance=opttolerance,
    )
    path_cmds = []
    for curve in path:
        sx, sy = curve.start_point
        cmd = f"M {_fmt(sx)} {_fmt(sy)}"
        for seg in curve:
            if seg.is_corner:
                cx, cy = seg.c
                ex, ey = seg.end_point
                cmd += f" L {_fmt(cx)} {_fmt(cy)} L {_fmt(ex)} {_fmt(ey)}"
            else:
                c1x, c1y = seg.c1
                c2x, c2y = seg.c2
                ex, ey = seg.end_point
                cmd += f" C {_fmt(c1x)} {_fmt(c1y)} {_fmt(c2x)} {_fmt(c2y)} {_fmt(ex)} {_fmt(ey)}"
        cmd += " Z"
        path_cmds.append(cmd)
    d = " ".join(path_cmds)
    svg_el = ET.Element(
        "svg",
        version="1.0",
        xmlns="http://www.w3.org/2000/svg",
        width=str(size),
        height=str(size),
        viewBox=f"0 0 {size} {size}",
        preserveAspectRatio="xMidYMid meet",
    )
    outer = ET.SubElement(svg_el, "g", fill="#000000", stroke="none")
    scale = min(size / width, size / height)
    tx = (size - width * scale) / 2
    ty = (size - height * scale) / 2
    inner = ET.SubElement(
        outer,
        "g",
        transform=f"translate({_fmt(tx)} {_fmt(ty)}) scale({_fmt(scale)})",
    )
    ET.SubElement(inner, "path", d=d)
    return ET.tostring(svg_el, encoding="unicode")


def apply_fill(
    svg: str,
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: float | None = None,
) -> str:
    """Apply fill and stroke styles to all paths in the SVG."""
    tree = ET.fromstring(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    for path in tree.findall(".//svg:path", ns):
        if fill:
            path.set("fill", fill)
        if stroke:
            path.set("stroke", stroke)
            if stroke_width is not None:
                path.set("stroke-width", _fmt(stroke_width))
        elif stroke_width is not None:
            path.set("stroke-width", _fmt(stroke_width))
    return ET.tostring(tree, encoding="unicode")
