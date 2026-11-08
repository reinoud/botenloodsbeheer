"""Het logo staat in de database, niet in de installatie (ADR-008, issue #186).

afbeelding laat weer soort 'logo' toe; de rij `logo` in instelling wijst naar de afbeelding. De
rechten van botenloods_web op afbeelding en instelling dekken uploaden en verwijderen al; de andere
rollen gebruiken het logo niet. De downgrade verwijdert een geüpload logo, want de oude regel laat
alleen foto's toe: een beheerder uploadt het na het terugzetten niet meer, het staat dan weer in
./huisstijl.

Revision ID: 0017
Revises: 0016
"""

from alembic import op

revision = '0017'
down_revision = '0016'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('soort_geldig', 'afbeelding', type_='check')
    op.create_check_constraint('soort_geldig', 'afbeelding', "soort IN ('foto', 'logo')")


def downgrade():
    op.execute("DELETE FROM instelling WHERE sleutel = 'logo'")
    op.execute("DELETE FROM afbeelding WHERE soort = 'logo'")
    op.drop_constraint('soort_geldig', 'afbeelding', type_='check')
    op.create_check_constraint('soort_geldig', 'afbeelding', "soort = 'foto'")
