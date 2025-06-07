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

## Web interface

Once the service is running you can visit
`http://localhost:8080/` in your browser for a simple GUI. The page lets you
upload an image or provide an image URL and tweak any query parameters before
submitting the request. The server response is shown next to the form as both
the raw SVG text and a rendered preview.

## API reference

### `POST /vectorize`

Convert an image to SVG. The image can be uploaded as multipart form data (`image` field) or specified via `image_url` query parameter. Every request must provide the API token in an `Authorization: Bearer <token>` header or as `token=<token>` in the query string.
Supported input types include PNG, JPEG, WebP, and any other format that Pillow can decode.

**Query parameters**



 
| name | type | default | options | description |
| --- | --- | --- | -- | ----- |
| `image_url` | str | `None` | `https://example.com/img.png` | <sub> URL of the image to vectorize when you are not uploading a file. The service downloads this remote image before processing. |
| `token` | str | – | `secret` | <sub >Authentication token for the request. Use this field if sending an `Authorization` header is inconvenient. |
| `threshold` | int | `128` | `64`, `128`, `200` | <sub> Brightness cutoff between 0 and 255 used to convert the image to black and white. Higher values treat more pixels as white before tracing. |
| `turnpolicy` | str | `minority` | `black`, `white`, `left`, `right`, `minority`, `majority`, `random` | <sub>Strategy Potrace uses to decide the direction of ambiguous turns. Different policies produce smoother, sharper, or more randomized paths. |
| `alphamax` | float | `1.0` | `0.0`, `1.0`, `2.0` | <sub>Parameter that balances curve smoothness against detail. Increasing this makes curves smoother at the expense of small features. |
| `turdsize` | int | `2` | `0`, `2`, `5` | <sub> Minimum size of speckles to keep in the output. Larger values remove more noise but may discard tiny details. |
| `size` | int | `250` | `100`, `250`, `500` | <sub> Width and height of the square SVG output. Bigger values yield a larger vector graphic. |
| `opticurve` | bool | `true` | `true`, `false` | <sub>Whether to apply Potrace's optimal curve fitting. Disable for raw, jagged paths. |
| `opttolerance` | float | `0.2` | `0.0`, `0.5`, `1.0` | <sub>How closely the curves match the bitmap. Lower values preserve detail, higher values simplify. |
| `background` | str | `None` | `#ffffff` | <sub>Background color to apply before tracing. Helpful for images with transparency. |
| `stroke` | str | `None` | `#000000` | <sub>Optional hex color for the stroke outline. |
| `stroke_width` | float | `1.0` | `0.5`, `1.0`, `2.0` | <sub>Width of the stroke when a stroke color is used. |
| `invert` | bool | `false` | `true`, `false` | <sub>Invert the image colors before vectorizing. |
| `passes` | int | `1` | `1`, `2`, `3` | <sub>Run multiple tracing passes to refine results. |
| `autocrop` | bool | `false` | `true`, `false` | <sub>Crop transparent edges before tracing. |
| `fill` | str | `None` | `#ff0000`, `#00ff00` | <sub> Optional hex color to fill the traced shapes. Leave unset for a transparent path. |
| `download` | bool | `false` | `true`, `false` | <sub> If `true`, the endpoint responds with a downloadable SVG file. Otherwise it returns a JSON body containing the SVG string. |




Responses:
- `200` JSON `{"svg": "<svg...>"}` or raw SVG if `download=true`
- `400` on invalid input or download errors
- `401` if authorization fails

When calling the API programmatically, make sure to parse the JSON body and
extract the `svg` field. Printing the raw HTTP response will show escaped
characters (like backslashes) around the SVG data, but parsing the JSON will
yield the clean `<svg...></svg>` string.

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
