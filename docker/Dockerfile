# Eigen stage zodat Dependabot het uv-image bijhoudt; het leest alleen FROM-regels (#105).
FROM ghcr.io/astral-sh/uv:0.9.5@sha256:f459f6f73a8c4ef5d69f4e6fbbdb8af751d6fa40ec34b39a1ab469acd6e289b7 AS uv

FROM python:3.14-slim@sha256:af8a5aa14780025dbfbcfbc81bd8a91ebd87711dd5b0f48ed71090949dd7cb1d AS app
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    FLASK_APP=app
# libpq uit Debian krijgt beveiligingsupdates; psycopg-binary leverde oude pcre en libcrypto mee (#86).
# shortcut: zlib1g uit Debian bijwerken (CVE-2026-85091), weg zodra het basisimage deb13u1 heeft.
RUN apt-get update && apt-get install --yes --no-install-recommends libpq5 zlib1g \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    uv sync --locked --no-dev
COPY alembic.ini ./
COPY migrations migrations
COPY app app
# Versie op de statuspagina (ADR-010); de workflow geeft de tag van de release mee.
ARG APP_VERSIE=ontwikkeling
ENV APP_VERSIE=$APP_VERSIE
# pip uit het basisimage is niet nodig (uv installeert) en brengt eigen kopieën van urllib3 en
# msgpack mee die trivy meldt (#59).
RUN pip uninstall --yes --no-cache-dir pip && useradd --system --uid 10001 app
USER 10001
EXPOSE 8000
# Toegangslog in het formaat zonder_code naar stdout (ADR-013); Traefik logt deze routes niet.
# Geen control socket: de standaardplek in de home is read-only en niemand gebruikt hem (#73).
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", \
     "--no-control-socket", "--logger-class", "app.toegangslog.Toegangslog", "app:create_app()"]

# Alleen voor ontwikkeling en tests: voegt pytest en ruff toe.
FROM app AS dev
USER root
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    uv sync --locked
COPY tests tests
USER 10001
