"""Indeling met rek, verdieping en vak (issue #80, ADR-003 v2.1.0).

Een plaats heet voortaan <rek>/<verdieping>/<vak>; code en volgorde vervallen als kolom (code is
afgeleid in models.py). De upgrade verwijdert alle plaatsen en rekken: er is nog geen installatie
in gebruik (besluit 2 van #80). plaats_bootsoort gaat mee via ON DELETE CASCADE; boten verliezen
alleen hun plaats. De downgrade verliest geen plaatsen: code wordt weer gevuld met de aanduiding
en volgorde met (verdieping - 1) * 12 + vak; de omschrijving van het rek vervalt.

Rechten: flask seed draait als botenloods_taken en voegt de bootsoort Wildwaterkano toe (besluit
25 van de backlog). Daarvoor krijgt die rol INSERT op bootsoort en gebruik van de reeks; de
downgrade trekt beide weer in (ADR-007: een nieuwe seedhandeling vraagt een eigen grant).

Revision ID: 0011
Revises: 0010
"""

import sqlalchemy as sa
from alembic import op

revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


ROL = "botenloods_taken"


def upgrade():
    op.execute(f"GRANT INSERT ON bootsoort TO {ROL}")
    op.execute(f"GRANT USAGE ON SEQUENCE bootsoort_id_seq TO {ROL}")
    op.execute("DELETE FROM plaats")
    op.execute("DELETE FROM rek")
    op.alter_column('rek', 'naam', type_=sa.String(length=10), existing_nullable=False)
    op.add_column('rek', sa.Column('omschrijving', sa.String(length=60), server_default='',
                                   nullable=False))
    op.create_index('uq_rek_naam', 'rek', [sa.text('lower(naam)')], unique=True)
    op.create_check_constraint('naam_geldig', 'rek', "naam <> '' AND naam NOT LIKE '%/%'")
    op.add_column('plaats', sa.Column('verdieping', sa.SmallInteger(), nullable=False))
    op.add_column('plaats', sa.Column('vak', sa.SmallInteger(), nullable=False))
    op.create_check_constraint('verdieping_geldig', 'plaats', 'verdieping BETWEEN 1 AND 5')
    op.create_check_constraint('vak_geldig', 'plaats', 'vak BETWEEN 1 AND 12')
    op.create_unique_constraint('uq_plaats_rek_verdieping_vak', 'plaats',
                                ['rek_id', 'verdieping', 'vak'])
    op.drop_index('uq_plaats_code', table_name='plaats')
    op.drop_column('plaats', 'code')
    op.drop_column('plaats', 'volgorde')


def downgrade():
    op.execute(f"REVOKE USAGE ON SEQUENCE bootsoort_id_seq FROM {ROL}")
    op.execute(f"REVOKE INSERT ON bootsoort FROM {ROL}")
    op.add_column('plaats', sa.Column('code', sa.String(length=20), nullable=True))
    op.add_column('plaats', sa.Column('volgorde', sa.Integer(), server_default=sa.text('0'),
                                      nullable=False))
    op.execute("UPDATE plaats SET code = rek.naam || '/' || plaats.verdieping || '/' || plaats.vak, "
               "volgorde = (plaats.verdieping - 1) * 12 + plaats.vak "
               "FROM rek WHERE rek.id = plaats.rek_id")
    op.alter_column('plaats', 'code', nullable=False)
    op.create_index('uq_plaats_code', 'plaats', [sa.text('lower(code)')], unique=True)
    op.drop_constraint('uq_plaats_rek_verdieping_vak', 'plaats', type_='unique')
    op.drop_constraint('vak_geldig', 'plaats', type_='check')
    op.drop_constraint('verdieping_geldig', 'plaats', type_='check')
    op.drop_column('plaats', 'vak')
    op.drop_column('plaats', 'verdieping')
    op.drop_column('rek', 'omschrijving')
    op.drop_constraint('naam_geldig', 'rek', type_='check')
    op.drop_index('uq_rek_naam', table_name='rek')
    op.alter_column('rek', 'naam', type_=sa.String(length=50), existing_nullable=False)
