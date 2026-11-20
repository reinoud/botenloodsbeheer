"""Een account koppelen aan een lid (ADR-015, issue #353).

Kolom beheerder.lid_id, nullable, met verwijzing beheerder_lid_id_fkey naar lid (ON DELETE SET NULL:
een opgeschoond lid wist de koppeling). Geen uniciteit en geen index. botenloods_taken verwijdert
kijkers met een oud-lid (ADR-007): SELECT op vier kolommen (WHERE en RETURNING) en DELETE; de cascades
naar passkey, uitnodiging en token draaien met de rechten van de eigenaar.

De downgrade trekt alle rechten van botenloods_taken op beheerder in (ook de kolomrechten; sinds 0010
had de rol er geen) en verwijdert de kolom: de koppelingen gaan verloren.

Revision ID: 0023
Revises: 0022
"""

import sqlalchemy as sa
from alembic import op

revision = '0023'
down_revision = '0022'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('beheerder', sa.Column('lid_id', sa.Integer(), nullable=True))
    op.create_foreign_key('beheerder_lid_id_fkey', 'beheerder', 'lid', ['lid_id'], ['id'],
                          ondelete='SET NULL')
    op.execute("GRANT SELECT (id, gebruikersnaam, rol, lid_id), DELETE ON beheerder TO botenloods_taken")


def downgrade():
    op.execute("REVOKE ALL ON beheerder FROM botenloods_taken")
    op.drop_column('beheerder', 'lid_id')
