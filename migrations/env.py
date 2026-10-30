"""Alembic draait als eigenaar van de database (DATABASE_URL van de dienst migrate)."""

import os

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from app.models import db

url = context.config.get_main_option("sqlalchemy.url") or os.environ["DATABASE_URL"]

# NullPool: geen verbinding blijft na de migratie in een pool openstaan.
with create_engine(url, poolclass=NullPool).connect() as verbinding:
    context.configure(connection=verbinding, target_metadata=db.metadata)
    with context.begin_transaction():
        context.run_migrations()
