"""Adres, telefoon en e-mail van leden en het tokenrecht persoonsgegevens vervallen (issue #180).

De kolommen verdwijnen uit lid; de ledenbron levert ze niet meer (#178). Het recht
persoonsgegevens gaat uit de rechten van elk token. Een actief token dat alleen dat recht had,
wordt ingetrokken, met een regel token.ingetrokken in het technische log (actor systeem/migratie);
tokens met andere rechten verliezen alleen dat recht, zonder logregel. Een ingetrokken token dat
alleen persoonsgegevens had, houdt het recht in de lijst: de check minstens_een_recht eist één recht.
Het token kan niets meer. De rollen en hun rechten op lid en token veranderen niet.

De downgrade zet de drie kolommen leeg terug. De verwijderde gegevens en het recht komen niet
terug: ingetrokken tokens blijven ingetrokken (ADR-005).

Revision ID: 0018
Revises: 0017
"""

import json

import sqlalchemy as sa
from alembic import op

revision = '0018'
down_revision = '0017'
branch_labels = None
depends_on = None

RECHT = 'persoonsgegevens'


def upgrade():
    verbinding = op.get_bind()
    alleen = verbinding.execute(sa.text(
        "UPDATE token SET ingetrokken_op = now() "
        "WHERE ingetrokken_op IS NULL AND rechten = ARRAY[:recht]::text[] RETURNING id, naam"
    ), {'recht': RECHT}).all()
    for token_id, naam in alleen:
        verbinding.execute(sa.text(
            "INSERT INTO logregel (soort, actor_soort, actor_id, actor_naam, actie, verwijzingen, gegevens) "
            "VALUES ('mutatie', 'systeem', NULL, 'migratie', 'token.ingetrokken', ARRAY[:ref], "
            "CAST(:gegevens AS jsonb))"
        ), {'ref': f'token:{token_id}',
            'gegevens': json.dumps({'naam': naam, 'reden': 'recht persoonsgegevens vervallen (#180)'})})
    op.execute(
        "UPDATE token SET rechten = array_remove(rechten, 'persoonsgegevens') "
        "WHERE 'persoonsgegevens' = ANY(rechten) AND cardinality(rechten) > 1")
    op.drop_column('lid', 'email')
    op.drop_column('lid', 'telefoon')
    op.drop_column('lid', 'adres')


def downgrade():
    op.add_column('lid', sa.Column('adres', sa.String(length=200), nullable=True))
    op.add_column('lid', sa.Column('telefoon', sa.String(length=30), nullable=True))
    op.add_column('lid', sa.Column('email', sa.String(length=254), nullable=True))
