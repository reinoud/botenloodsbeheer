"""Slice 1a: beheerders, inloggen, mutatielog, instelling en taakrun.

De database-rollen botenloods_web en botenloods_taken krijgen alleen de rechten die ze nodig
hebben. Op logregel mag web alleen lezen en toevoegen; taken mag ook verwijderen (ADR-006).

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

TABELLEN = ("beheerder", "passkey", "uitnodiging", "instelling", "taakrun")


def upgrade():
    op.create_table('beheerder',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('naam', sa.String(length=100), nullable=False),
    sa.Column('gebruikersnaam', sa.String(length=50), nullable=False),
    sa.Column('actief', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('sessieversie', sa.Integer(), server_default=sa.text('1'), nullable=False),
    sa.Column('wachtwoordhash', sa.Text(), nullable=True),
    sa.Column('totp_geheim', sa.LargeBinary(), nullable=True),
    sa.Column('laatste_totp_stap', sa.BigInteger(), nullable=True),
    sa.Column('mislukte_pogingen', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('geblokkeerd_tot', sa.DateTime(timezone=True), nullable=True),
    sa.Column('aangemaakt_op', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('(wachtwoordhash IS NULL) = (totp_geheim IS NULL)', name='wachtwoord_met_totp'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('gebruikersnaam')
    )
    op.create_table('instelling',
    sa.Column('sleutel', sa.String(length=50), nullable=False),
    sa.Column('waarde', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('sleutel')
    )
    op.create_table('logregel',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('tijdstip', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('soort', sa.String(length=10), nullable=False),
    sa.Column('actor_soort', sa.String(length=20), nullable=False),
    sa.Column('actor_id', sa.Integer(), nullable=True),
    sa.Column('actor_naam', sa.String(length=100), nullable=False),
    sa.Column('actie', sa.String(length=50), nullable=False),
    sa.Column('verwijzingen', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=False),
    sa.Column('gegevens', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.CheckConstraint("soort IN ('mutatie', 'api')", name='soort_geldig'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_logregel_tijdstip', 'logregel', ['tijdstip'], unique=False)
    op.create_index('ix_logregel_verwijzingen', 'logregel', ['verwijzingen'], unique=False, postgresql_using='gin')
    op.create_table('taakrun',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('taak', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('aangevraagd_op', sa.DateTime(timezone=True), nullable=True),
    sa.Column('gestart_op', sa.DateTime(timezone=True), nullable=True),
    sa.Column('beeindigd_op', sa.DateTime(timezone=True), nullable=True),
    sa.Column('aantallen', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('foutmelding', sa.Text(), nullable=True),
    sa.CheckConstraint("status IN ('aangevraagd', 'bezig', 'geslaagd', 'mislukt')", name='status_geldig'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('passkey',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('beheerder_id', sa.Integer(), nullable=False),
    sa.Column('credential_id', sa.LargeBinary(), nullable=False),
    sa.Column('publieke_sleutel', sa.LargeBinary(), nullable=False),
    sa.Column('teller', sa.BigInteger(), nullable=False),
    sa.Column('naam', sa.String(length=100), nullable=False),
    sa.Column('aangemaakt_op', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('laatst_gebruikt_op', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['beheerder_id'], ['beheerder.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('credential_id')
    )
    op.create_table('uitnodiging',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('beheerder_id', sa.Integer(), nullable=False),
    sa.Column('code_hash', sa.String(length=64), nullable=False),
    sa.Column('verloopt_op', sa.DateTime(timezone=True), nullable=False),
    sa.Column('gebruikt_op', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['beheerder_id'], ['beheerder.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code_hash')
    )

    # Rollen bestaan normaal al (docker/db-init.sh); zonder login aanmaken als ze ontbreken.
    op.execute("""
        DO $$ BEGIN
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'botenloods_web') THEN
            CREATE ROLE botenloods_web NOLOGIN;
          END IF;
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'botenloods_taken') THEN
            CREATE ROLE botenloods_taken NOLOGIN;
          END IF;
        END $$
    """)
    for rol in ("botenloods_web", "botenloods_taken"):
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {', '.join(TABELLEN)} TO {rol}")
        op.execute(f"GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO {rol}")
        op.execute(f"GRANT SELECT ON alembic_version TO {rol}")
    op.execute("GRANT SELECT, INSERT ON logregel TO botenloods_web")
    op.execute("GRANT SELECT, INSERT, DELETE ON logregel TO botenloods_taken")


def downgrade():
    for rol in ("botenloods_web", "botenloods_taken"):
        op.execute(f"REVOKE ALL ON alembic_version FROM {rol}")
        op.execute(f"REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM {rol}")
    op.drop_table('uitnodiging')
    op.drop_table('passkey')
    op.drop_table('taakrun')
    op.drop_index('ix_logregel_verwijzingen', table_name='logregel', postgresql_using='gin')
    op.drop_index('ix_logregel_tijdstip', table_name='logregel')
    op.drop_table('logregel')
    op.drop_table('instelling')
    op.drop_table('beheerder')
