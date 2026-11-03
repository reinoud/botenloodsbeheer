"""Slice 9: api leest plaats en bootsoort voor GET /api/v1/bootaantallen (BLB-009, ADR-012).

De opschoning (ADR-006) vraagt geen nieuwe rechten: botenloods_taken mag al DELETE op logregel,
lid, boot en afbeelding.

Revision ID: 0008
Revises: 0007
"""

from alembic import op

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("GRANT SELECT ON plaats, bootsoort TO botenloods_api")


def downgrade():
    op.execute("REVOKE SELECT ON plaats, bootsoort FROM botenloods_api")
