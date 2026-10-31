"""Slice 6: de import van leden via de API (ADR-012).

Alleen botenloods_api maakt leden aan en werkt ze bij, en legt de uitkomst van een import vast
in taakrun. De worker verliest het recht om leden aan te maken of bij te werken; hij houdt
SELECT en DELETE voor de opschoning (ADR-006, ADR-007). web leest lid en zet een importverzoek
in taakrun, zoals sinds slice 1.

Revision ID: 0006
Revises: 0005
"""

from alembic import op

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("GRANT SELECT, INSERT, UPDATE ON lid, taakrun TO botenloods_api")
    op.execute("GRANT USAGE ON SEQUENCE lid_id_seq, taakrun_id_seq TO botenloods_api")
    op.execute("REVOKE INSERT, UPDATE ON lid FROM botenloods_taken")


def downgrade():
    op.execute("GRANT INSERT, UPDATE ON lid TO botenloods_taken")
    op.execute("REVOKE ALL ON lid, taakrun FROM botenloods_api")
    op.execute("REVOKE ALL ON SEQUENCE lid_id_seq, taakrun_id_seq FROM botenloods_api")
