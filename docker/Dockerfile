FROM python:3.14-slim AS app
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    FLASK_APP=app
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=from=ghcr.io/astral-sh/uv:0.9.5,source=/uv,target=/bin/uv \
    uv sync --locked --no-dev
COPY alembic.ini ./
COPY migrations migrations
COPY app app
RUN useradd --system --uid 10001 app
USER 10001
EXPOSE 8000
# Toegangslog in het formaat zonder_code naar stdout (ADR-013); Traefik logt deze routes niet.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", \
     "--logger-class", "app.toegangslog.Toegangslog", "app:create_app()"]

# Alleen voor ontwikkeling en tests: voegt pytest en ruff toe.
FROM app AS dev
USER root
RUN --mount=from=ghcr.io/astral-sh/uv:0.9.5,source=/uv,target=/bin/uv \
    uv sync --locked
COPY tests tests
USER 10001
