"""DELETE op verdieping_bootsoort vervalt voor botenloods_web (issue #85, ADR-003 v2.2.1).

Geen code verwijdert rijen uit de tabel; de cascades vanuit rek en bootsoort draaien als eigenaar
van de tabel. De downgrade geeft het recht terug.

Revision ID: 0013
Revises: 0012
"""

from alembic import op

revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("REVOKE DELETE ON verdieping_bootsoort FROM botenloods_web")


def downgrade():
    op.execute("GRANT DELETE ON verdieping_bootsoort TO botenloods_web")
