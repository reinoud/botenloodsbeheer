"""De instelbare kleuren vervallen: de rijen kleur_primair en kleur_secundair verdwijnen (issue #150).

De app volgt de Dajaks-huisstijl (ADR-002 v1.2.0, besluit stakeholder 2026-11-06). De naam blijft.

Revision ID: 0015
Revises: 0014
"""

from alembic import op

revision = '0015'
down_revision = '0014'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DELETE FROM instelling WHERE sleutel IN ('kleur_primair', 'kleur_secundair')")


def downgrade():
    pass  # de oude kleuren zijn niet te herstellen; de app kent ze niet meer
