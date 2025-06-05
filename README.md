# vectorize-svc

FastAPI micro-service for converting raster images to SVG paths using [potrace](http://potrace.sourceforge.net/). It exposes a single HTTP endpoint that accepts an image file or URL and returns the traced SVG data.

## Quick start with Docker

```bash
# build the container and start the service
docker-compose up --build
```

This will launch the app on [http://localhost:8080](http://localhost:8080).

## API reference

### `POST /vectorize`

Convert an image to SVG. The image can be uploaded as multipart form data (`image` field) or specified via `image_url` query parameter. If `API_TOKEN` is set, include an `Authorization: Bearer <token>` header.

**Query parameters**

| name | type | default | description |
| --- | --- | --- | --- |
| `threshold` | int | `128` | Binarization threshold (0–255) |
| `turnpolicy` | str | `minority` | Potrace turn policy |
| `alphamax` | float | `1.0` | AlphaMax parameter |
| `turdsize` | int | `2` | Suppress speckles smaller than this |
| `fill` | str | `None` | Optional fill color (e.g. `#ff0000`) |
| `download` | bool | `false` | Return SVG as attachment |

Responses:
- `200` JSON `{"svg": "<svg...>"}` or raw SVG if `download=true`
- `400` on invalid input or download errors
- `401` if authorization fails

### `GET /healthz`

Simple liveness probe returning `{"status": "ok"}`.

### cURL examples

```bash
# local file
curl -F image=@test.png http://localhost:8080/vectorize

# via URL
curl -X POST "http://localhost:8080/vectorize?image_url=https://example.com/img.png"

# download result
curl -F image=@test.png "http://localhost:8080/vectorize?download=true" -o out.svg
```

## Environment variables

- `API_TOKEN` (optional) – Bearer token required for calls to `/vectorize` when set.

## Deployment

1. `docker build -t vectorize-svc .`
2. `docker run -d -p 8080:8080 --env API_TOKEN=secret vectorize-svc`
3. Point your reverse proxy to port 8080

## Development & testing

Install the system libraries required to build `pypotrace`:

```bash
apt-get install -y pkg-config libagg-dev libpotrace-dev
```

Then install Python dependencies and run tests:

```bash
pip install -r requirements.txt
pytest
```

`httpx` is included in `requirements.txt` for the `fastapi.testclient` used in the test suite.
