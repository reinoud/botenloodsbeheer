"""Een boot heeft een eigenaar, is clubboot of heeft een onbekende eigenaar (issue #204).

boot krijgt de kolom clubboot (NOT NULL, standaard false) en de controle lid_of_clubboot: een boot
met een lid is nooit clubboot. Geen lid en geen clubboot is "eigenaar onbekend". Tot nu toe was
geen lid een clubboot; de migratie zet daarom elke bestaande boot zonder lid op clubboot (besluit
stakeholder 2026-11-10). Rechten: de tabellen hebben rechten op tabelniveau, de nieuwe kolom
volgt; er verandert niets aan de rollen.

De downgrade haalt controle en kolom weg. Een boot met een onbekende eigenaar is dan, zoals voor
deze migratie, een boot zonder lid en geldt als clubboot; die toestand kan niet terug.

Revision ID: 0019
Revises: 0018
"""

import sqlalchemy as sa
from alembic import op

revision = '0019'
down_revision = '0018'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('boot', sa.Column('clubboot', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.execute("UPDATE boot SET clubboot = true WHERE lid_id IS NULL")
    op.create_check_constraint('lid_of_clubboot', 'boot', 'NOT (lid_id IS NOT NULL AND clubboot)')


def downgrade():
    op.drop_constraint('lid_of_clubboot', 'boot', type_='check')
    op.drop_column('boot', 'clubboot')
