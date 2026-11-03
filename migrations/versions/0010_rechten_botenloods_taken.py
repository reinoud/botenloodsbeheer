"""Rechten van botenloods_taken beperkt tot wat de worker en flask seed gebruiken (issue #60).

De migraties 0001 en 0002 gaven de rol dezelfde DML als botenloods_web. De worker schrijft
taakrun en schoont logregel, lid, boot en afbeelding op (ADR-006, ADR-007); flask seed draait ook
als deze rol en maakt instelling, rek, plaats, plaats_bootsoort, boot, wachtlijst en logregel aan
en wijst plaatsen toe. bootsoort houdt UPDATE omdat FOR KEY SHARE (boot en plaats aanmaken) dat
recht vraagt, ook al wijzigt de worker de rij niet. De downgrade zet de rechten van 0009 terug.

Revision ID: 0010
Revises: 0009
"""

from alembic import op

revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None

ROL = "botenloods_taken"
# Per tabel de rechten die vervallen; de downgrade geeft ze terug.
INGETROKKEN = {
    "beheerder": "SELECT, INSERT, UPDATE, DELETE",
    "passkey": "SELECT, INSERT, UPDATE, DELETE",
    "uitnodiging": "SELECT, INSERT, UPDATE, DELETE",
    "instelling": "UPDATE, DELETE",
    "rek": "UPDATE, DELETE",
    "plaats_bootsoort": "UPDATE, DELETE",
    "plaats": "DELETE",
    "bootsoort": "INSERT, DELETE",
    "afbeelding": "INSERT, UPDATE",
    "taakrun": "DELETE",
}
# Reeksen van tabellen waarin de worker niets meer aanmaakt (lid sinds 0006).
REEKSEN = ("afbeelding_id_seq", "beheerder_id_seq", "bootsoort_id_seq", "lid_id_seq",
           "passkey_id_seq", "uitnodiging_id_seq")


def upgrade():
    for tabel, rechten in INGETROKKEN.items():
        op.execute(f"REVOKE {rechten} ON {tabel} FROM {ROL}")
    op.execute(f"REVOKE USAGE ON SEQUENCE {', '.join(REEKSEN)} FROM {ROL}")


def downgrade():
    op.execute(f"GRANT USAGE ON SEQUENCE {', '.join(REEKSEN)} TO {ROL}")
    for tabel, rechten in INGETROKKEN.items():
        op.execute(f"GRANT {rechten} ON {tabel} TO {ROL}")
