"""Herstel slice 1b (#9): de webrol leest leden alleen, en de plaatscode is uniek zonder
onderscheid in hoofdletters.

Leden schrijft alleen de worker, ook bij flask seed (ADR-004). Een dubbele plaatscode met
andere hoofdletters weigert nu ook de database, zodat twee gelijktijdige aanvragen niet allebei
slagen.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("REVOKE INSERT, UPDATE, DELETE ON lid FROM botenloods_web")
    op.drop_constraint('plaats_code_key', 'plaats', type_='unique')
    op.create_index('uq_plaats_code', 'plaats', [sa.text('lower(code)')], unique=True)


def downgrade():
    op.drop_index('uq_plaats_code', table_name='plaats')
    op.create_unique_constraint('plaats_code_key', 'plaats', ['code'])
    op.execute("GRANT INSERT, UPDATE, DELETE ON lid TO botenloods_web")
