from __future__ import annotations

import os

from fastapi import FastAPI, File, UploadFile, Query, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from .core.tracing import apply_fill, raster_to_svg

app = FastAPI(title="vectorize-svc")

# cache API token so we don't hit the environment on every request
API_TOKEN = os.getenv("API_TOKEN")


def _check_auth(request: Request) -> None:
    """Validate Authorization header against the API token if configured."""
    header = request.headers.get("Authorization")
    if API_TOKEN and header != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/vectorize")
async def vectorize(
    request: Request,
    image: UploadFile = File(...),
    threshold: int = Query(128, ge=0, le=255),
    turnpolicy: str = Query("minority"),
    alphamax: float = Query(1.0),
    turdsize: int = Query(2),
    fill: str | None = Query(None),
    download: bool = Query(False),
) -> Response | JSONResponse:
    _check_auth(request)
    content = await image.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")
    try:
        svg = raster_to_svg(content, threshold, turnpolicy, alphamax, turdsize)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if fill:
        svg = apply_fill(svg, fill)
    if download:
        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={
                "Content-Disposition": (
                    "attachment; filename=vectorized.svg"
                )
            },
        )
    return JSONResponse({"svg": svg})


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
