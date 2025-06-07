from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Query, HTTPException, Request
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import urllib.request

from .core.tracing import apply_fill, raster_to_svg

app = FastAPI(title="vectorize-svc")
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Serve the front-end HTML page."""
    return FileResponse(BASE_DIR / "static" / "index.html")


# cache API token so we don't hit the environment on every request
API_TOKEN = os.getenv("API_TOKEN")


def _check_auth(request: Request) -> None:
    """Validate auth token from header or query string if configured."""
    header = request.headers.get("Authorization")
    token_param = request.query_params.get("token")
    if API_TOKEN and not (header == f"Bearer {API_TOKEN}" or token_param == API_TOKEN):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/vectorize", response_model=None)
async def vectorize(
    request: Request,
    image: UploadFile | None = File(None),
    image_url: str | None = Query(None),
    threshold: int = Query(128, ge=0, le=255),
    turnpolicy: str = Query("minority"),
    alphamax: float = Query(1.0),
    turdsize: int = Query(2),
    size: int = Query(250, gt=0),
    opticurve: bool = Query(True),
    opttolerance: float = Query(0.2),
    background: str | None = Query(None),
    stroke: str | None = Query(None),
    stroke_width: float = Query(1.0),
    invert: bool = Query(False),
    passes: int = Query(1, ge=1),
    autocrop: bool = Query(False),
    fill: str | None = Query(None),
    download: bool = Query(False),
) -> Response | JSONResponse:
    _check_auth(request)
    if image_url:
        if not image_url.lower().startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="Invalid image_url")

        def _download(url: str) -> bytes:
            with urllib.request.urlopen(url, timeout=10) as resp:
                return resp.read()

        try:
            content = await asyncio.to_thread(_download, image_url)
        except Exception as exc:  # pragma: no cover - network errors
            raise HTTPException(
                status_code=400, detail="Failed to fetch image"
            ) from exc
    else:
        if image is None:
            raise HTTPException(status_code=400, detail="No image provided")
        content = await image.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")
    try:
        svg = raster_to_svg(
            content,
            threshold,
            turnpolicy,
            alphamax,
            turdsize,
            size,
            opticurve,
            opttolerance,
            background,
            invert,
            passes,
            autocrop,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if fill or stroke or stroke_width:
        svg = apply_fill(svg, fill, stroke, stroke_width)
    if download:
        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={"Content-Disposition": ("attachment; filename=vectorized.svg")},
        )
    return JSONResponse({"svg": svg})


@app.get("/vectorize", response_model=None)
async def vectorize_get(
    request: Request,
    image_url: str = Query(...),
    threshold: int = Query(128, ge=0, le=255),
    turnpolicy: str = Query("minority"),
    alphamax: float = Query(1.0),
    turdsize: int = Query(2),
    size: int = Query(250, gt=0),
    opticurve: bool = Query(True),
    opttolerance: float = Query(0.2),
    background: str | None = Query(None),
    stroke: str | None = Query(None),
    stroke_width: float = Query(1.0),
    invert: bool = Query(False),
    passes: int = Query(1, ge=1),
    autocrop: bool = Query(False),
    fill: str | None = Query(None),
    download: bool = Query(False),
) -> Response | JSONResponse:
    """Vectorize an image from a URL via a GET request."""
    return await vectorize(
        request=request,
        image=None,
        image_url=image_url,
        threshold=threshold,
        turnpolicy=turnpolicy,
        alphamax=alphamax,
        turdsize=turdsize,
        size=size,
        opticurve=opticurve,
        opttolerance=opttolerance,
        background=background,
        stroke=stroke,
        stroke_width=stroke_width,
        invert=invert,
        passes=passes,
        autocrop=autocrop,
        fill=fill,
        download=download,
    )


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
