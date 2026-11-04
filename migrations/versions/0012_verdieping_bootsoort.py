"""Bootsoort per verdieping (issue #83, ADR-003 v2.2.0).

Het rek onthoudt per verdieping hooguit één bootsoort; een nieuwe plaats op die verdieping krijgt
haar. Bestaande rekken krijgen geen rijen en bestaande plaatsen veranderen niet. De downgrade
verwijdert alleen de tabel: plaatsen houden hun bootsoorten. Alleen botenloods_web schrijft de
tabel (rek aanmaken, indeling instellen); flask seed (botenloods_taken) kent geen keuze per
verdieping en de rol api raakt de indeling niet.

Revision ID: 0012
Revises: 0011
"""

import sqlalchemy as sa
from alembic import op

revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'verdieping_bootsoort',
        sa.Column('rek_id', sa.Integer(), sa.ForeignKey('rek.id', ondelete='CASCADE'),
                  primary_key=True),
        sa.Column('verdieping', sa.SmallInteger(), primary_key=True),
        sa.Column('bootsoort_id', sa.Integer(), sa.ForeignKey('bootsoort.id', ondelete='CASCADE'),
                  nullable=False),
        sa.CheckConstraint('verdieping BETWEEN 1 AND 5', name='verdieping_geldig'),
    )
    op.execute("GRANT SELECT, INSERT, DELETE ON verdieping_bootsoort TO botenloods_web")


def downgrade():
    op.drop_table('verdieping_bootsoort')
