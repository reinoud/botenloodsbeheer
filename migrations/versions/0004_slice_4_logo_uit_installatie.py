"""Slice 4: het logo staat in de installatie, niet in de applicatie (ADR-008, issue #17).

Verwijdert een in slice 3 geüpload logo uit afbeelding en de rij logo uit instelling, en laat in
afbeelding alleen nog foto's toe. De downgrade zet de oude regel terug, maar niet het logo: dat
staat voortaan in ./huisstijl.

Revision ID: 0004
Revises: 0003
"""

from alembic import op

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DELETE FROM instelling WHERE sleutel = 'logo'")
    op.execute("DELETE FROM afbeelding WHERE soort = 'logo'")
    op.drop_constraint('soort_geldig', 'afbeelding', type_='check')
    op.create_check_constraint('soort_geldig', 'afbeelding', "soort = 'foto'")


def downgrade():
    op.drop_constraint('soort_geldig', 'afbeelding', type_='check')
    op.create_check_constraint('soort_geldig', 'afbeelding', "soort IN ('foto', 'logo')")
