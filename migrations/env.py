"""Alembic draait als eigenaar van de database (DATABASE_URL van de dienst migrate)."""

import os

from alembic import context
from sqlalchemy import create_engine

from app.models import db

url = context.config.get_main_option("sqlalchemy.url") or os.environ["DATABASE_URL"]

with create_engine(url).connect() as verbinding:
    context.configure(connection=verbinding, target_metadata=db.metadata)
    with context.begin_transaction():
        context.run_migrations()
