"""Zoeken zonder onderscheid in accenten (issue #232).

De extensie unaccent van PostgreSQL (een vertrouwde extensie) haalt accenten uit kolom en
zoektekst, zodat 'jose' het lid 'José' vindt en andersom. De migratie draait als eigenaar van de
database; de rollen web, api en worker hoeven niets te kunnen: de functie is voor iedereen
uitvoerbaar en de rollen maken zelf geen extensie. Geen tabelrechten of gegevens wijzigen.

Revision ID: 0021
Revises: 0020
"""

from alembic import op

revision = '0021'
down_revision = '0020'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade():
    op.execute("DROP EXTENSION IF EXISTS unaccent")
