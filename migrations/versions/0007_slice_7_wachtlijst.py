"""Slice 7: de wachtlijst per bootsoort (BLB-013, architectuur §3).

web zet boten op de lijst en haalt ze eraf; de worker ook, voor seed en de opschoning. Geen
rol mag UPDATE: de aanmelddatum is achteraf niet te wijzigen (intake). api haalt bij een import de boten van oud-leden van
de lijst en leest daarvoor ook boot (BLB-008, ADR-004). Een verwijderde boot gaat via de
cascade van de lijst.

Revision ID: 0007
Revises: 0006
"""

import sqlalchemy as sa
from alembic import op

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('wachtlijst',
    sa.Column('boot_id', sa.Integer(), nullable=False),
    sa.Column('aangemeld_op', sa.Date(), nullable=False),
    sa.ForeignKeyConstraint(['boot_id'], ['boot.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('boot_id')
    )
    for rol in ("botenloods_web", "botenloods_taken"):
        op.execute(f"GRANT SELECT, INSERT, DELETE ON wachtlijst TO {rol}")
    op.execute("GRANT SELECT, DELETE ON wachtlijst TO botenloods_api")
    op.execute("GRANT SELECT ON boot TO botenloods_api")


def downgrade():
    op.execute("REVOKE SELECT ON boot FROM botenloods_api")
    op.drop_table('wachtlijst')
