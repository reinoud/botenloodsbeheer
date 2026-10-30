"""Slice 1b: indeling, bootsoorten met de startlijst, leden, boten en afbeeldingen.

Web en worker krijgen dezelfde rechten op de nieuwe tabellen; de worker synchroniseert de leden
en ruimt later oud-leden op (ADR-004, ADR-006).

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

TABELLEN = ("rek", "bootsoort", "plaats_bootsoort", "plaats", "lid", "boot", "afbeelding")
# Startlijst uit de intake (ADR-009); aanpassen is BLB-028.
BOOTSOORTEN = ("Kajak", "Canadese kano", "Surfski", "C11", "Supboard")


def upgrade():
    op.create_table('afbeelding',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('soort', sa.String(length=10), nullable=False),
    sa.Column('mime_type', sa.String(length=20), nullable=False),
    sa.Column('inhoud', sa.LargeBinary(), nullable=False),
    sa.Column('breedte', sa.Integer(), nullable=False),
    sa.Column('hoogte', sa.Integer(), nullable=False),
    sa.Column('sleutel', sa.String(length=16), nullable=False),
    sa.CheckConstraint("soort IN ('foto', 'logo')", name='soort_geldig'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('sleutel')
    )
    bootsoort = op.create_table('bootsoort',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('naam', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('naam')
    )
    op.create_table('lid',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lidnummer', sa.String(length=20), nullable=False),
    sa.Column('naam', sa.String(length=100), nullable=False),
    sa.Column('adres', sa.String(length=200), nullable=True),
    sa.Column('telefoon', sa.String(length=30), nullable=True),
    sa.Column('email', sa.String(length=254), nullable=True),
    sa.Column('lid_sinds', sa.Date(), nullable=True),
    sa.Column('opzegdatum', sa.Date(), nullable=True),
    sa.Column('uit_bron_op', sa.Date(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('lidnummer')
    )
    op.create_table('rek',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('naam', sa.String(length=50), nullable=False),
    sa.Column('volgorde', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('boot',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('naam', sa.String(length=100), nullable=False),
    sa.Column('bootsoort_id', sa.Integer(), nullable=False),
    sa.Column('lid_id', sa.Integer(), nullable=True),
    sa.Column('afbeelding_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['afbeelding_id'], ['afbeelding.id'], ),
    sa.ForeignKeyConstraint(['bootsoort_id'], ['bootsoort.id'], ),
    sa.ForeignKeyConstraint(['lid_id'], ['lid.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('afbeelding_id')
    )
    op.create_index(op.f('ix_boot_lid_id'), 'boot', ['lid_id'], unique=False)
    op.create_table('plaats',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('rek_id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('publieke_sleutel', sa.String(length=10), nullable=False),
    sa.Column('is_clubplaats', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('volgorde', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('boot_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['boot_id'], ['boot.id'], ),
    sa.ForeignKeyConstraint(['rek_id'], ['rek.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('boot_id'),
    sa.UniqueConstraint('code'),
    sa.UniqueConstraint('publieke_sleutel')
    )
    op.create_index(op.f('ix_plaats_rek_id'), 'plaats', ['rek_id'], unique=False)
    op.create_table('plaats_bootsoort',
    sa.Column('plaats_id', sa.Integer(), nullable=False),
    sa.Column('bootsoort_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['bootsoort_id'], ['bootsoort.id'], ),
    sa.ForeignKeyConstraint(['plaats_id'], ['plaats.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('plaats_id', 'bootsoort_id')
    )
    op.bulk_insert(bootsoort, [{"naam": naam} for naam in BOOTSOORTEN])

    for rol in ("botenloods_web", "botenloods_taken"):
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {', '.join(TABELLEN)} TO {rol}")
        op.execute(f"GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO {rol}")


def downgrade():
    op.drop_table('plaats_bootsoort')
    op.drop_index(op.f('ix_plaats_rek_id'), table_name='plaats')
    op.drop_table('plaats')
    op.drop_index(op.f('ix_boot_lid_id'), table_name='boot')
    op.drop_table('boot')
    op.drop_table('rek')
    op.drop_table('lid')
    op.drop_table('bootsoort')
    op.drop_table('afbeelding')
