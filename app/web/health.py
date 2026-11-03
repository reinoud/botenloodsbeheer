"""Health endpoints zonder inloggen en zonder details (ADR-010)."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from flask import Blueprint
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.models import db

health = Blueprint("health", __name__)

_INI = Path(__file__).resolve().parents[2] / "alembic.ini"
HEAD = ScriptDirectory.from_config(Config(str(_INI))).get_current_head()


@health.get("/health/live")
def live():
    return {"status": "ok"}


@health.get("/health/ready")
def ready():
    try:
        versie = db.session.execute(text("SELECT version_num FROM alembic_version")).scalar()
    except SQLAlchemyError:
        db.session.rollback()
        versie = None
    if versie != HEAD:
        return {"status": "niet gereed"}, 503
    return {"status": "ok"}
