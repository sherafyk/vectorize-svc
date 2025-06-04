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
from PIL import Image
import potrace

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
) -> str:
    """Convert raster image bytes to an SVG string."""
    try:
        image = Image.open(io.BytesIO(data))
    except Exception as exc:  # pragma: no cover - invalid image
        raise ValueError("Invalid image") from exc
    gray = image.convert("L")
    width, height = gray.size
    arr = np.array(gray)
    bitmap = potrace.Bitmap(arr > threshold)
    path = bitmap.trace(
        turdsize=turdsize,
        turnpolicy=TURNPOLICIES.get(turnpolicy, potrace.TURNPOLICY_MINORITY),
        alphamax=alphamax,
    )
    path_cmds = []
    for curve in path:
        sx, sy = curve.start_point
        cmd = f"M {sx} {sy}"
        for seg in curve:
            if seg.is_corner:
                cx, cy = seg.c
                ex, ey = seg.end_point
                cmd += f" L {cx} {cy} L {ex} {ey}"
            else:
                c1x, c1y = seg.c1
                c2x, c2y = seg.c2
                ex, ey = seg.end_point
                cmd += f" C {c1x} {c1y} {c2x} {c2y} {ex} {ey}"
        cmd += " Z"
        path_cmds.append(cmd)
    d = " ".join(path_cmds)
    svg_el = ET.Element(
        "svg",
        xmlns="http://www.w3.org/2000/svg",
        width=str(width),
        height=str(height),
    )
    ET.SubElement(svg_el, "path", d=d, fill="black", stroke="none")
    return ET.tostring(svg_el, encoding="unicode")


def apply_fill(svg: str, fill: str | None = None) -> str:
    """Apply a fill color to all paths in the SVG."""
    tree = ET.fromstring(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    for path in tree.findall(".//svg:path", ns):
        if fill:
            path.set("fill", fill)
    return ET.tostring(tree, encoding="unicode")
