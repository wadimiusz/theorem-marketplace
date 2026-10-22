FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev cron curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# Create cron file running sync_bounties.py at minute 0 of every hour
RUN echo "0 * * * * root /app/.venv/bin/python /app/sync_bounties.py >> /var/log/cron.log 2>&1" > /etc/cron.d/sync_bounties \
    && chmod 0644 /etc/cron.d/sync_bounties \
    && crontab /etc/cron.d/sync_bounties

EXPOSE 5000

CMD bash -c "cron && exec uv run gunicorn --bind 0.0.0.0:5000 --threads 4 --timeout 120 --access-logfile - --error-logfile - --log-level info app:app"
