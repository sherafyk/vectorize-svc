# vectorize-svc

FastAPI micro-service for converting raster images to SVG paths using [potrace](http://potrace.sourceforge.net/). It exposes a single HTTP endpoint that accepts an image file or URL and returns the traced SVG data. Any format supported by Pillow (PNG, JPEG, WebP, etc.) can be used as input.

## Quick start with Docker

```bash
# build the container and start the service
docker-compose up --build
```
> [!TIP]
> ### Useful Snippets
> ```
> git pull origin main
> ```
> > Pull the latest changes
> 
> ```
> docker-compose down
> docker-compose up -d --build
> ```
> > `down` stops and removes the old containers.  
> > `up -d --build` rebuilds the image with the new code, starts the containers in the background.
> 
> ```
> docker-compose ps
> ```
> > Check if it’s running: Look for “Up” in the STATUS column.
>
> ```
> docker-compose logs -f
> ```
> > Check logs  
> 
 > ```
 > curl http://localhost:8080/healthz
 > ```
 > > Test endpoint

This will launch the app on [http://localhost:8080](http://localhost:8080).
`docker-compose.yml` sets a default `API_TOKEN` of `changeme`. You can change
this value, but authentication is always required. Every call to `/vectorize`
must include the token using one of the following methods:
1. `Authorization: Bearer <token>` header
2. `token=<token>` query parameter

## API reference

### `POST /vectorize`

Convert an image to SVG. The image can be uploaded as multipart form data (`image` field) or specified via `image_url` query parameter. Every request must provide the API token in an `Authorization: Bearer <token>` header or as `token=<token>` in the query string.
Supported input types include PNG, JPEG, WebP, and any other format that Pillow can decode.

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

### `GET /vectorize`

Vectorize an image by specifying its `image_url` in the query string. This makes
it possible to call the service directly from a web browser. The same query
parameters as the POST endpoint are supported and the response format is
identical. The authentication token is required; include `token=<token>` in the
query string or send the `Authorization` header when calling this endpoint. This
is especially handy when pasting the URL directly into a browser:

```
http://localhost:8080/vectorize?image_url=https://example.com/img.png&token=secret
```

### `GET /healthz`

Simple liveness probe returning `{"status": "ok"}`.

### cURL examples

```bash
# local file
curl -H "Authorization: Bearer secret" -F image=@test.png \
  http://localhost:8080/vectorize

# via URL
curl -X POST \
  -H "Authorization: Bearer secret" \
  "http://localhost:8080/vectorize?image_url=https://example.com/img.png"

# GET request
http://localhost:8080/vectorize?image_url=https://example.com/img.png&token=secret

# GET request with token (browser)
http://localhost:8080/vectorize?image_url=https://example.com/img.png&token=secret

# download result
curl -H "Authorization: Bearer secret" \
  -F image=@test.png "http://localhost:8080/vectorize?download=true" -o out.svg
```

## Environment variables

- `API_TOKEN` – Bearer token that **must** be supplied with every call to `/vectorize`.
  Each request must include the token using one of two methods:
  1. `Authorization: Bearer <token>` header
  2. `token=<token>` query parameter

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
