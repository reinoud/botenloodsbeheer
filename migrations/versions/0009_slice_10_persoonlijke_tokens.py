"""Slice 10: persoonlijke tokens en de leesaanroepen (ADR-005 v1.4.0, ADR-012 v1.6.0).

token krijgt beheerder_id (persoonlijk, ON DELETE CASCADE) en gemaakt_door (tekst, zodat de maker
van een robottoken zichtbaar blijft na vertrek). De cascade draait met de rechten van de eigenaar
van de tabel, dus web krijgt geen DELETE op token. api leest of de eigenaar actief is en leest rek
en plaats_bootsoort voor GET /api/v1/plaatsen.

Revision ID: 0009
Revises: 0008
"""

import sqlalchemy as sa
from alembic import op

revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('token', sa.Column('beheerder_id', sa.Integer(), nullable=True))
    op.add_column('token', sa.Column('gemaakt_door', sa.String(length=50), nullable=False,
                                     server_default='cli'))
    op.alter_column('token', 'gemaakt_door', server_default=None)
    op.create_foreign_key('token_beheerder_id_fkey', 'token', 'beheerder', ['beheerder_id'],
                          ['id'], ondelete='CASCADE')
    op.create_check_constraint('persoonlijk_met_beheerder', 'token',
                               "(soort = 'persoonlijk') = (beheerder_id IS NOT NULL)")
    op.execute("GRANT SELECT (id, actief) ON beheerder TO botenloods_api")
    op.execute("GRANT SELECT ON rek, plaats_bootsoort TO botenloods_api")


def downgrade():
    op.execute("REVOKE SELECT ON rek, plaats_bootsoort FROM botenloods_api")
    op.execute("REVOKE SELECT (id, actief) ON beheerder FROM botenloods_api")
    # Persoonlijke tokens bestonden vóór 0009 niet; zonder eigenaar mogen ze niet blijven werken.
    op.execute("DELETE FROM token WHERE soort = 'persoonlijk'")
    op.drop_constraint('persoonlijk_met_beheerder', 'token', type_='check')
    op.drop_constraint('token_beheerder_id_fkey', 'token', type_='foreignkey')
    op.drop_column('token', 'gemaakt_door')
    op.drop_column('token', 'beheerder_id')
