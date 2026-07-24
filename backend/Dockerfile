FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.production.txt .
RUN pip install --no-cache-dir -r requirements.production.txt

COPY . .
RUN chmod +x /app/docker-entrypoint.sh \
    && addgroup --system django \
    && adduser --system --ingroup django django \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R django:django /app

USER django
EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
