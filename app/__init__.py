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

    # Nginx is de enige vertrouwde proxy en overschrijft X-Forwarded-For (architectuur §8.1).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=app.config["PROXY_HOPS"], x_proto=1)

    db.init_app(app)
    csrf.init_app(app)

    from app import cli, web

    app.register_blueprint(web.bp)
    app.register_blueprint(web.health)
    cli.registreer(app)
    web.huisstijl.logo_laden(app)
    return app
