"""Oud-leden zonder boot weg (issue #203).

De ledenimport nam een oud-lid op dat nog niet in de applicatie stond. Besluit stakeholder
2026-11-10: een lid met een opzegdatum op of vóór de migratiedag en zonder boot wordt verwijderd
(dataminimalisatie). Oud-leden met een boot blijven, zodat de boot als boot van een oud-lid wordt
herkend. Mee gaan de rijen van naamkoppeling die naar het lid verwijzen (ON DELETE CASCADE);
boot.lid_id heeft geen cascade, maar de gekozen leden hebben geen boot. Logregels met
lid:<id> zijn tekst en blijven staan. Rechten veranderen niet: de migratie draait als eigenaar.

De downgrade is een no-op: de verwijderde gegevens komen niet terug. De volgende import maakt
ze ook niet opnieuw aan.

Revision ID: 0020
Revises: 0019
"""

from alembic import op

revision = '0020'
down_revision = '0019'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DELETE FROM lid WHERE opzegdatum <= CURRENT_DATE "
               "AND NOT EXISTS (SELECT 1 FROM boot WHERE boot.lid_id = lid.id)")


def downgrade():
    pass  # verwijderde oud-leden komen niet terug
