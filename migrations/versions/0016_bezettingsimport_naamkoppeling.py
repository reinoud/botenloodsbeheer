"""De lopende bezettingsimport en de onthouden naamkoppelingen (issue #158, ADR-014 §3 en §4).

bezettingsimport: hooguit één rij, afgedwongen met een unieke kolom `enige` die altijd waar is;
verdwijnt met de beheerder die uploadde. naamkoppeling: naam naar lid (ON DELETE CASCADE) of
clubboot. botenloods_web mag lezen, aanmaken, wijzigen (ook FOR UPDATE) en verwijderen;
botenloods_taken leest en verwijdert (de opschoning van verlopen imports en oude koppelingen);
botenloods_api heeft geen recht. De cascades draaien als eigenaar van de tabel.

Revision ID: 0016
Revises: 0015
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = '0016'
down_revision = '0015'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('bezettingsimport',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('enige', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('beheerder_id', sa.Integer(), nullable=False),
    sa.Column('aangemaakt_op', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('verloopt_op', sa.DateTime(timezone=True), nullable=False),
    sa.Column('regels', postgresql.JSONB(), nullable=False),
    sa.Column('keuzes', postgresql.JSONB(), server_default='{}', nullable=False),
    sa.CheckConstraint('enige', name='enige_waar'),
    sa.ForeignKeyConstraint(['beheerder_id'], ['beheerder.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('enige')
    )
    op.create_table('naamkoppeling',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('naam', sa.String(length=100), nullable=False),
    sa.Column('lid_id', sa.Integer(), nullable=True),
    sa.Column('clubboot', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('gebruikt_op', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('(lid_id IS NOT NULL) <> clubboot', name='lid_of_clubboot'),
    sa.ForeignKeyConstraint(['lid_id'], ['lid.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('naam')
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON bezettingsimport, naamkoppeling "
               "TO botenloods_web")
    op.execute("GRANT USAGE ON SEQUENCE bezettingsimport_id_seq, naamkoppeling_id_seq "
               "TO botenloods_web")
    op.execute("GRANT SELECT, DELETE ON bezettingsimport, naamkoppeling TO botenloods_taken")


def downgrade():
    # De rechten verdwijnen met de tabellen.
    op.drop_table('naamkoppeling')
    op.drop_table('bezettingsimport')
