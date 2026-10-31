"""Slice 5: tabel token en de databaserol botenloods_api (ADR-005, ADR-012).

web maakt tokens en trekt ze in (de CLI draait in web). api leest tokens, werkt alleen
laatst_gebruikt_op bij en schrijft de logregel van elke aanroep. De schrijfrechten op lid gaan
pas in slice 6 naar api, met de import.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('token',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('naam', sa.String(length=50), nullable=False),
    sa.Column('soort', sa.String(length=12), nullable=False),
    sa.Column('prefix', sa.String(length=8), nullable=False),
    sa.Column('hash', sa.String(length=64), nullable=False),
    sa.Column('rechten', postgresql.ARRAY(sa.Text()), nullable=False),
    sa.Column('ip_whitelist', postgresql.ARRAY(postgresql.CIDR()), server_default='{}',
              nullable=False),
    sa.Column('aangemaakt_op', sa.DateTime(timezone=True), server_default=sa.text('now()'),
              nullable=False),
    sa.Column('verloopt_op', sa.DateTime(timezone=True), nullable=False),
    sa.Column('ingetrokken_op', sa.DateTime(timezone=True), nullable=True),
    sa.Column('laatst_gebruikt_op', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("soort IN ('persoonlijk', 'robot')", name='soort_geldig'),
    sa.CheckConstraint('cardinality(rechten) > 0', name='minstens_een_recht'),
    sa.CheckConstraint("soort <> 'robot' OR cardinality(ip_whitelist) > 0",
                       name='robot_met_whitelist'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('naam'),
    sa.UniqueConstraint('prefix')
    )

    # De rol bestaat normaal al (docker/db-init.sh); zonder login aanmaken als hij ontbreekt.
    op.execute("""
        DO $$ BEGIN
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'botenloods_api') THEN
            CREATE ROLE botenloods_api NOLOGIN;
          END IF;
        END $$
    """)
    op.execute("GRANT SELECT, INSERT, UPDATE ON token TO botenloods_web")
    op.execute("GRANT USAGE ON SEQUENCE token_id_seq TO botenloods_web")
    op.execute("GRANT SELECT, UPDATE (laatst_gebruikt_op) ON token TO botenloods_api")
    op.execute("GRANT SELECT, INSERT ON logregel TO botenloods_api")
    op.execute("GRANT USAGE ON SEQUENCE logregel_id_seq TO botenloods_api")
    op.execute("GRANT SELECT ON alembic_version TO botenloods_api")  # /health/ready


def downgrade():
    op.drop_table('token')
    op.execute("REVOKE ALL ON logregel, alembic_version FROM botenloods_api")
    op.execute("REVOKE ALL ON SEQUENCE logregel_id_seq FROM botenloods_api")
