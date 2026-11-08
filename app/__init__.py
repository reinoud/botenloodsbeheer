"""Botenloodsbeheer: Flask-applicatie."""

import json
import logging
import sys

from flask import Flask, abort, request
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.routing import IntegerConverter

from app import config
from app.models import db

csrf = CSRFProtect()
# Bovengrens van integer in PostgreSQL; een groter getal geeft daar een fout en dus een 500.
INT_MAX = 2**31 - 1


class _Id(IntegerConverter):
    """<int:...> met de bovengrens van integer in PostgreSQL: een groter id geeft 404, geen 500 (#67)."""

    def __init__(self, url_map, **kwargs):
        kwargs.setdefault("max", INT_MAX)
        super().__init__(url_map, **kwargs)


class _JsonLog(logging.Formatter):
    def format(self, record):
        regel = {"tijd": self.formatTime(record), "niveau": record.levelname,
                 "bron": record.name, "bericht": record.getMessage()}
        if record.exc_info:  # zonder traceback is een 500 in productie niet te herleiden (#137)
            tekst = self.formatException(record.exc_info)
            for detail in _details(record.exc_info[1]):
                tekst = tekst.replace(detail, "[weggelaten]")
            regel["traceback"] = tekst
        return json.dumps(regel, ensure_ascii=False)


def _details(fout):
    """De DETAIL van PostgreSQL in de keten van een uitzondering: de rij of sleutel van een fout,
    met persoonsgegevens. Letterlijk, want een veldwaarde kan een regelovergang bevatten."""
    gezien = set()
    while fout is not None and id(fout) not in gezien:
        gezien.add(id(fout))
        for f in (fout, getattr(fout, "orig", None)):
            detail = getattr(getattr(f, "diag", None), "message_detail", None)
            if detail:
                yield detail
        fout = fout.__cause__ or fout.__context__


def create_app(overrides=None):
    app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
    app.url_map.converters["int"] = _Id
    app.config.update(config.laad())
    app.config.update(overrides or {})

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonLog())
    logging.basicConfig(level=app.config["LOG_NIVEAU"], handlers=[handler], force=True)
    logging.getLogger("alembic").setLevel(logging.WARNING)

    # Traefik is de enige vertrouwde proxy en overschrijft X-Forwarded-For (ADR-013).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=app.config["PROXY_HOPS"], x_proto=1)

    @app.before_request
    def gecodeerd_pad_weigeren():
        # Traefik kiest de router op het gecodeerde pad (%2F blijft staan), Werkzeug decodeert het.
        # Geen route heeft procentcodering nodig; zo omzeilt niemand de rate limit (ADR-013, #65).
        # RAW_URI zet Gunicorn en ook de testclient; shortcut: andere servers zonder RAW_URI
        # laten alles door, de app draait alleen achter Gunicorn.
        if "%" in request.environ.get("RAW_URI", "").split("?", 1)[0]:
            abort(400)
        # PostgreSQL weigert een NUL-teken in tekst; zonder deze controle wordt dat een 500 (#67).
        if any("\x00" in v for vs in request.values.listvalues() for v in vs):
            abort(400)

    db.init_app(app)
    csrf.init_app(app)

    from app import cli, web

    if app.config["DIENST"] == "api":
        # Alleen de dienst api kent /api/v1; web en worker niet (ADR-012).
        from app import api

        app.register_blueprint(api.bp)
        csrf.exempt(api.bp)  # token in de header, geen cookie: CSRF speelt niet (ADR-005)
        app.logger.info("API staat %s (API_INGESCHAKELD).",
                        "aan" if app.config["API_INGESCHAKELD"] else "uit")
    else:
        app.register_blueprint(web.bp)
    app.register_blueprint(web.health)
    cli.registreer(app)
    return app
