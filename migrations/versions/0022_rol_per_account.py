"""Rol per account: beheerder of kijker (ADR-015, issue #322).

Kolom rol (VARCHAR(10) NOT NULL) met de check rol_geldig. Bestaande accounts worden beheerder via
een tijdelijke server default; die vervalt direct, zodat een vergeten rol een fout geeft. api leest
de rol voor de tokencontrole (eigenaar moet beheerder zijn). De tabelrechten van botenloods_web
(0001) dekken de kolom al; botenloods_taken heeft sinds 0010 geen recht op beheerder.

De downgrade blokkeert eerst elke kijker (actief = false, sessieversie plus een), met per account
een regel beheerder.geblokkeerd van actor systeem 'migratie': zonder kolom wordt elke kijker anders
beheerder. Na een nieuwe upgrade zijn dat geblokkeerde beheerders. Met de kolom vervalt ook haar recht.

Revision ID: 0022
Revises: 0021
"""

import sqlalchemy as sa
from alembic import op

revision = '0022'
down_revision = '0021'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('beheerder', sa.Column('rol', sa.String(length=10), nullable=False,
                                         server_default='beheerder'))
    op.alter_column('beheerder', 'rol', server_default=None)
    op.create_check_constraint('rol_geldig', 'beheerder', "rol IN ('beheerder', 'kijker')")
    op.execute("GRANT SELECT (rol) ON beheerder TO botenloods_api")


def downgrade():
    op.execute("""
        INSERT INTO logregel (soort, actor_soort, actor_id, actor_naam, actie, verwijzingen, gegevens)
        SELECT 'mutatie', 'systeem', NULL, 'migratie', 'beheerder.geblokkeerd',
               ARRAY['beheerder:' || id], jsonb_build_object('gebruikersnaam', gebruikersnaam)
        FROM beheerder WHERE rol = 'kijker' AND actief
    """)
    op.execute("UPDATE beheerder SET actief = false, sessieversie = sessieversie + 1 "
               "WHERE rol = 'kijker'")
    op.drop_constraint('rol_geldig', 'beheerder', type_='check')
    op.drop_column('beheerder', 'rol')
