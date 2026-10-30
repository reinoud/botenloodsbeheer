"""Alle tabellen (architectuur §4). Slice 1a: beheerders, inloggen, log en techniek."""

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    LargeBinary,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

Tijdstip = DateTime(timezone=True)


class Beheerder(db.Model):
    __tablename__ = "beheerder"
    __table_args__ = (
        # Een wachtwoord zonder TOTP bestaat niet (ADR-001).
        CheckConstraint(
            "(wachtwoordhash IS NULL) = (totp_geheim IS NULL)", name="wachtwoord_met_totp"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    naam: Mapped[str] = mapped_column(String(100))
    gebruikersnaam: Mapped[str] = mapped_column(String(50), unique=True)
    actief: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    sessieversie: Mapped[int] = mapped_column(default=1, server_default=text("1"))
    wachtwoordhash: Mapped[str | None] = mapped_column(Text)
    totp_geheim: Mapped[bytes | None] = mapped_column(LargeBinary)  # Fernet-versleuteld
    laatste_totp_stap: Mapped[int | None] = mapped_column(BigInteger)
    mislukte_pogingen: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    geblokkeerd_tot: Mapped[datetime | None] = mapped_column(Tijdstip)
    aangemaakt_op: Mapped[datetime] = mapped_column(Tijdstip, server_default=func.now())

    passkeys: Mapped[list["Passkey"]] = relationship(back_populates="beheerder")


class Passkey(db.Model):
    __tablename__ = "passkey"

    id: Mapped[int] = mapped_column(primary_key=True)
    beheerder_id: Mapped[int] = mapped_column(ForeignKey("beheerder.id", ondelete="CASCADE"))
    credential_id: Mapped[bytes] = mapped_column(LargeBinary, unique=True)
    publieke_sleutel: Mapped[bytes] = mapped_column(LargeBinary)
    teller: Mapped[int] = mapped_column(BigInteger)
    naam: Mapped[str] = mapped_column(String(100))
    aangemaakt_op: Mapped[datetime] = mapped_column(Tijdstip, server_default=func.now())
    laatst_gebruikt_op: Mapped[datetime | None] = mapped_column(Tijdstip)

    beheerder: Mapped[Beheerder] = relationship(back_populates="passkeys")


class Uitnodiging(db.Model):
    __tablename__ = "uitnodiging"

    id: Mapped[int] = mapped_column(primary_key=True)
    beheerder_id: Mapped[int] = mapped_column(ForeignKey("beheerder.id", ondelete="CASCADE"))
    code_hash: Mapped[str] = mapped_column(String(64), unique=True)  # sha256, hex
    verloopt_op: Mapped[datetime] = mapped_column(Tijdstip)
    gebruikt_op: Mapped[datetime | None] = mapped_column(Tijdstip)

    beheerder: Mapped[Beheerder] = relationship()


class Logregel(db.Model):
    """Alleen toevoegen; de webgebruiker heeft geen UPDATE of DELETE (ADR-006)."""

    __tablename__ = "logregel"
    __table_args__ = (
        CheckConstraint("soort IN ('mutatie', 'api')", name="soort_geldig"),
        Index("ix_logregel_tijdstip", "tijdstip"),
        Index("ix_logregel_verwijzingen", "verwijzingen", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tijdstip: Mapped[datetime] = mapped_column(Tijdstip, server_default=func.now())
    soort: Mapped[str] = mapped_column(String(10))
    actor_soort: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[int | None]
    actor_naam: Mapped[str] = mapped_column(String(100))
    actie: Mapped[str] = mapped_column(String(50))
    verwijzingen: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default="{}")
    gegevens: Mapped[dict] = mapped_column(JSONB, server_default="{}")


class Instelling(db.Model):
    __tablename__ = "instelling"

    sleutel: Mapped[str] = mapped_column(String(50), primary_key=True)
    waarde: Mapped[str] = mapped_column(Text)


class Taakrun(db.Model):
    __tablename__ = "taakrun"
    __table_args__ = (
        CheckConstraint(
            "status IN ('aangevraagd', 'bezig', 'geslaagd', 'mislukt')", name="status_geldig"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    taak: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20))
    aangevraagd_op: Mapped[datetime | None] = mapped_column(Tijdstip)
    gestart_op: Mapped[datetime | None] = mapped_column(Tijdstip)
    beeindigd_op: Mapped[datetime | None] = mapped_column(Tijdstip)
    aantallen: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    foutmelding: Mapped[str | None] = mapped_column(Text)
