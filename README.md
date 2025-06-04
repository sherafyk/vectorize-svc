# vectorize-svc

FastAPI micro-service converting raster images to SVG using potrace.

```bash
# build and run locally
docker-compose up --build
```

### cURL examples

```bash
# inline SVG
curl -F image=@test.png http://localhost:8080/vectorize

# download
curl -F image=@test.png "http://localhost:8080/vectorize?download=true" -o out.svg
```

### Environment

- `API_TOKEN` optional bearer token for `/vectorize`

### Deploy checklist

1. `docker build -t vectorize-svc .`
2. `docker run -d -p 8080:8080 --env API_TOKEN=secret vectorize-svc`
3. Point your reverse proxy to port 8080
