FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends     gcc g++ libpq-dev python3-dev     && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends     libpq5     && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/*     && rm -rf /wheels

COPY . .

CMD ["python", "main.py"]
