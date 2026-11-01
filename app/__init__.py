"""Botenloodsbeheer: Flask-applicatie."""

import json
import logging
import sys

from flask import Flask
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

from app import config
from app.models import db

csrf = CSRFProtect()


class _JsonLog(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {"tijd": self.formatTime(record), "niveau": record.levelname,
             "bron": record.name, "bericht": record.getMessage()},
            ensure_ascii=False,
        )


def create_app(overrides=None):
    app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
    app.config.update(config.laad())
    app.config.update(overrides or {})

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonLog())
    logging.basicConfig(level=app.config["LOG_NIVEAU"], handlers=[handler], force=True)
    logging.getLogger("alembic").setLevel(logging.WARNING)

    # Traefik is de enige vertrouwde proxy en overschrijft X-Forwarded-For (ADR-013).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=app.config["PROXY_HOPS"], x_proto=1)

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
        web.huisstijl.logo_laden(app)
    app.register_blueprint(web.health)
    cli.registreer(app)
    return app
