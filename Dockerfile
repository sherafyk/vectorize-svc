FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libagg-dev potrace libpotrace-dev pkg-config && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    potrace libagg2 libpotrace0 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
COPY . /app
WORKDIR /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
