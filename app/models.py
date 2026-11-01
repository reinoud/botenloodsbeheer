"""Alle tabellen (architectuur §4). Slice 1a: beheerders, inloggen, log en techniek.
Slice 1b: indeling, bootsoorten, leden, boten en afbeeldingen. Slice 5: token. Slice 7: wachtlijst."""

from datetime import date, datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    LargeBinary,
    String,
    Table,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, CIDR, JSONB
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

    # Verwijderen laat de database de passkeys opruimen (ON DELETE CASCADE).
    passkeys: Mapped[list["Passkey"]] = relationship(
        back_populates="beheerder", passive_deletes=True, order_by="Passkey.id"
    )


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


# Indeling, leden en boten (slice 1b)


class Rek(db.Model):
    __tablename__ = "rek"

    id: Mapped[int] = mapped_column(primary_key=True)
    naam: Mapped[str] = mapped_column(String(50))
    volgorde: Mapped[int] = mapped_column(default=0, server_default=text("0"))

    plaatsen: Mapped[list["Plaats"]] = relationship(
        back_populates="rek", order_by="Plaats.volgorde, Plaats.id"
    )


class Bootsoort(db.Model):
    """Een tabel, zodat BLB-028 later geen migratie vraagt. Startlijst in migratie 0002."""

    __tablename__ = "bootsoort"

    id: Mapped[int] = mapped_column(primary_key=True)
    naam: Mapped[str] = mapped_column(String(50), unique=True)


plaats_bootsoort = Table(
    "plaats_bootsoort",
    db.metadata,
    Column("plaats_id", ForeignKey("plaats.id", ondelete="CASCADE"), primary_key=True),
    Column("bootsoort_id", ForeignKey("bootsoort.id"), primary_key=True),
)


class Plaats(db.Model):
    """Drie identiteiten (ADR-003): id intern, publieke_sleutel in de QR-link, code voor mensen."""

    __tablename__ = "plaats"

    id: Mapped[int] = mapped_column(primary_key=True)
    rek_id: Mapped[int] = mapped_column(ForeignKey("rek.id"), index=True)
    code: Mapped[str] = mapped_column(String(20))  # uniek zonder hoofdletters: zie __table_args__
    publieke_sleutel: Mapped[str] = mapped_column(String(10), unique=True)
    is_clubplaats: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    volgorde: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    boot_id: Mapped[int | None] = mapped_column(ForeignKey("boot.id"), unique=True)

    rek: Mapped[Rek] = relationship(back_populates="plaatsen")
    bootsoorten: Mapped[list[Bootsoort]] = relationship(
        secondary=plaats_bootsoort, order_by=Bootsoort.id
    )
    boot: Mapped["Boot | None"] = relationship(back_populates="plaats")

    __table_args__ = (Index("uq_plaats_code", func.lower(code), unique=True),)


class Lid(db.Model):
    """Alleen de synchronisatie wijzigt een lid (ADR-004). Oud-lid is afgeleid (domein/leden)."""

    __tablename__ = "lid"

    id: Mapped[int] = mapped_column(primary_key=True)
    lidnummer: Mapped[str] = mapped_column(String(20), unique=True)
    naam: Mapped[str] = mapped_column(String(100))
    adres: Mapped[str | None] = mapped_column(String(200))
    telefoon: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(254))
    lid_sinds: Mapped[date | None] = mapped_column(Date)
    opzegdatum: Mapped[date | None] = mapped_column(Date)
    uit_bron_op: Mapped[date | None] = mapped_column(Date)

    boten: Mapped[list["Boot"]] = relationship(back_populates="lid", order_by="Boot.naam")


class Afbeelding(db.Model):
    """Foto als bytea (ADR-008). De sleutel staat in de URL en wijzigt per upload. Het logo
    staat niet hier maar in de installatie."""

    __tablename__ = "afbeelding"
    __table_args__ = (CheckConstraint("soort = 'foto'", name="soort_geldig"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    soort: Mapped[str] = mapped_column(String(10))
    mime_type: Mapped[str] = mapped_column(String(20))
    inhoud: Mapped[bytes] = mapped_column(LargeBinary)
    breedte: Mapped[int]
    hoogte: Mapped[int]
    sleutel: Mapped[str] = mapped_column(String(16), unique=True)


class Boot(db.Model):
    """Een clubboot heeft geen lid."""

    __tablename__ = "boot"

    id: Mapped[int] = mapped_column(primary_key=True)
    naam: Mapped[str] = mapped_column(String(100))
    bootsoort_id: Mapped[int] = mapped_column(ForeignKey("bootsoort.id"))
    lid_id: Mapped[int | None] = mapped_column(ForeignKey("lid.id"), index=True)
    afbeelding_id: Mapped[int | None] = mapped_column(ForeignKey("afbeelding.id"), unique=True)

    bootsoort: Mapped[Bootsoort] = relationship()
    lid: Mapped[Lid | None] = relationship(back_populates="boten")
    afbeelding: Mapped[Afbeelding | None] = relationship()
    plaats: Mapped[Plaats | None] = relationship(back_populates="boot")
    # Verwijderen van de boot haalt hem van de wachtlijst (ON DELETE CASCADE).
    wachtlijst: Mapped["Wachtlijst | None"] = relationship(
        back_populates="boot", cascade="all, delete-orphan", passive_deletes=True)


class Wachtlijst(db.Model):
    """Een boot hooguit één keer; de bootsoort volgt uit de boot, dus elke soort heeft vanzelf een
    eigen lijst (architectuur §3). De aanmelddatum is achteraf niet te wijzigen (intake)."""

    __tablename__ = "wachtlijst"

    boot_id: Mapped[int] = mapped_column(ForeignKey("boot.id", ondelete="CASCADE"), primary_key=True)
    aangemeld_op: Mapped[date] = mapped_column(Date)

    boot: Mapped[Boot] = relationship(back_populates="wachtlijst")


class Token(db.Model):
    """API-token (ADR-005). De waarde staat nergens; alleen de prefix en een SHA-256-hash.
    Persoonlijke tokens (met beheerder) volgen in slice 10."""

    __tablename__ = "token"
    __table_args__ = (
        CheckConstraint("soort IN ('persoonlijk', 'robot')", name="soort_geldig"),
        CheckConstraint("cardinality(rechten) > 0", name="minstens_een_recht"),
        CheckConstraint("soort <> 'robot' OR cardinality(ip_whitelist) > 0",
                        name="robot_met_whitelist"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    naam: Mapped[str] = mapped_column(String(50), unique=True)
    soort: Mapped[str] = mapped_column(String(12))
    prefix: Mapped[str] = mapped_column(String(8), unique=True)
    hash: Mapped[str] = mapped_column(String(64))  # sha256 van het hele token, hex
    rechten: Mapped[list[str]] = mapped_column(ARRAY(Text))
    ip_whitelist: Mapped[list] = mapped_column(ARRAY(CIDR), server_default="{}")
    aangemaakt_op: Mapped[datetime] = mapped_column(Tijdstip, server_default=func.now())
    verloopt_op: Mapped[datetime] = mapped_column(Tijdstip)
    ingetrokken_op: Mapped[datetime | None] = mapped_column(Tijdstip)
    laatst_gebruikt_op: Mapped[datetime | None] = mapped_column(Tijdstip)
