"""botenloods_api ziet en wijzigt in taakrun alleen zijn eigen taken (issue #24, ADR-012 v1.7.0).

Een rijbeleid laat de API alleen rijen met taak ledenimport of bootaantallen lezen, aanmaken en
wijzigen, zodat hij de hartslag van de worker niet kan vervalsen. Het beleid voor de andere rollen
laat alles toe; de eigenaar valt buiten het rijbeleid. De downgrade haalt het weg.

Revision ID: 0014
Revises: 0013
"""

from alembic import op

revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE taakrun ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY alle_rollen ON taakrun USING (true)")
    op.execute("CREATE POLICY api_eigen_taken ON taakrun AS RESTRICTIVE TO botenloods_api "
               "USING (taak IN ('ledenimport', 'bootaantallen'))")


def downgrade():
    op.execute("DROP POLICY api_eigen_taken ON taakrun")
    op.execute("DROP POLICY alle_rollen ON taakrun")
    op.execute("ALTER TABLE taakrun DISABLE ROW LEVEL SECURITY")
