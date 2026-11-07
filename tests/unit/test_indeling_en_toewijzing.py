"""Rekken en plaatsen (BLB-001, nieuwe indeling: test_indeling_vakken.py), boten (BLB-005), toewijzen (BLB-010) en de openbare
leesfunctie (BLB-020). Elke mutatie geeft een logregel (ADR-006)."""

import io
import re
import threading
from datetime import date, timedelta

import pytest
from PIL import Image
from sqlalchemy import create_engine, func, select, text

from app.domein import CLI, Regelfout, afbeeldingen, boten, indeling, log, toewijzing
from app.models import Afbeelding, Boot, Logregel, Plaats, Rek, db
from tests.unit.conftest import WEB
from tests.unit.hulp import lid, png
from tests.unit.hulp import plaats as plaats_aanmaken


def soort(naam):
    return next(s.id for s in indeling.bootsoorten() if s.naam == naam)


def plaats(code="A/1/1", soorten=("Kajak",), club=False):
    return plaats_aanmaken(code, [soort(s) for s in soorten], club)


def boot(lid_id=None, bootsoort="Kajak", naam="Zeemeeuw", foto=None):
    return boten.boot_aanmaken(naam, soort(bootsoort), lid_id, foto, CLI)


def acties():
    return [r.actie for r in db.session.scalars(select(Logregel).order_by(Logregel.id))]


# Indeling


def test_startlijst_bootsoorten(app):
    assert [s.naam for s in indeling.bootsoorten()] == [
        "Kajak", "Canadese kano", "Surfski", "C11", "Supboard"]


def test_rek_en_plaats_aanmaken_met_publieke_sleutel(app):
    p = plaats(soorten=("Kajak", "Surfski"), club=True)
    assert [r.naam for r in indeling.rekken()] == ["A"]
    assert p.is_clubplaats and [s.naam for s in p.bootsoorten] == ["Kajak", "Surfski"]
    assert re.fullmatch(r"[2-9a-km-np-zA-HJ-NP-Z]{10}", p.publieke_sleutel)
    assert p.code not in p.publieke_sleutel and str(p.id) not in p.publieke_sleutel
    assert acties() == ["rek.aangemaakt", "plaats.aangemaakt", "plaats.gewijzigd"]


def test_publieke_sleutels_zijn_verschillend(app):
    sleutels = {plaats(f"A/{v}/{k}").publieke_sleutel for v in range(1, 6) for k in range(1, 7)}
    assert len(sleutels) == 30


def test_rek_wijzigen_en_leeg_rek_verwijderen(app):
    p = plaats()
    indeling.rek_wijzigen(p.rek_id, "Noord", "", CLI)
    assert indeling.rek(p.rek_id).naam == "Noord"
    indeling.rek_verwijderen(p.rek_id, CLI)
    assert db.session.scalar(select(func.count()).select_from(Plaats)) == 0
    assert db.session.scalar(select(func.count()).select_from(Rek)) == 0
    assert acties()[-2:] == ["rek.gewijzigd", "rek.verwijderd"]


def test_rek_met_bezette_plaats_niet_te_verwijderen(app):
    p = plaats()
    toewijzing.toewijzen(p.id, boot(lid().id).id, CLI)
    with pytest.raises(Regelfout, match="Geef eerst die plaatsen vrij"):
        indeling.rek_verwijderen(p.rek_id, CLI)
    assert db.session.get(Plaats, p.id).boot_id is not None


def test_plaats_verwijderen_bestaat_niet_meer(app):
    """BLB-044: een plaats verdwijnt alleen via het raster (issue #83)."""
    assert not hasattr(indeling, "plaats_verwijderen")


# Boten


@pytest.mark.parametrize("veld", ["opzegdatum", "uit_bron_op"])
def test_geen_nieuwe_boot_voor_oud_lid(app, veld):
    oud = lid(**{veld: date.today() - timedelta(days=1)})
    with pytest.raises(Regelfout, match="is oud-lid en krijgt geen nieuwe boot"):
        boot(oud.id)
    assert db.session.scalar(select(func.count()).select_from(Boot)) == 0


def test_boot_van_lid_en_clubboot(app):
    anna = lid()
    b1, b2 = boot(anna.id), boot(anna.id, naam="Fuut")
    club = boot(None, naam="Clubkajak")
    assert {b.naam for b in anna.boten} == {"Zeemeeuw", "Fuut"}
    assert club.lid is None
    assert acties() == ["boot.aangemaakt"] * 3
    assert log.regels([f"lid:{anna.id}"])[0].verwijzingen == [f"boot:{b2.id}", f"lid:{anna.id}"]
    assert b1.id != b2.id


# MPO: een JPEG met een tweede beeld, zoals sommige telefoons die maken (#70).
@pytest.mark.parametrize("formaat, extra", [
    ("JPEG", {}), ("MPO", {"save_all": True, "append_images": [Image.new("RGB", (60, 40))]})],
    ids=["jpeg", "mpo"])
def test_foto_wordt_verkleind_en_zonder_exif_opgeslagen(app, formaat, extra):
    exif = Image.Exif()
    exif[0x010F] = "Telefoonmerk"  # Make
    bron = png(3200, 2000, exif=exif.tobytes(), formaat=formaat, comment=b"Vakantie bij oma",
               icc=b"bron-kleurprofiel", **extra)
    assert Image.open(io.BytesIO(bron)).format == formaat
    b = boot(lid().id, foto=bron)
    foto = Image.open(io.BytesIO(b.afbeelding.inhoud))
    assert foto.format == "JPEG" and max(foto.size) == 1600
    assert getattr(foto, "n_frames", 1) == 1 and "mp" not in foto.info
    assert not foto.getexif() and b"Telefoonmerk" not in b.afbeelding.inhoud
    assert "comment" not in foto.info and b"Vakantie bij oma" not in b.afbeelding.inhoud
    assert "icc_profile" not in foto.info and b"bron-kleurprofiel" not in b.afbeelding.inhoud
    assert len(b.afbeelding.sleutel) == 16


@pytest.mark.parametrize("formaat", ["TIFF", "GIF", "BMP"])
def test_andere_formaten_worden_niet_eens_gedecodeerd(app, formaat):
    # Zonder formats= opent Pillow elk geregistreerd formaat en weigert pas daarna.
    with pytest.raises(Regelfout, match="geen geldige afbeelding in JPEG, PNG of WebP"):
        afbeeldingen.verwerk(png(formaat=formaat))


@pytest.mark.parametrize("inhoud", [b"geen afbeelding",
                                    b'<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                                    png(formaat="GIF")])
def test_ongeldige_foto_geweigerd_en_vorige_blijft(app, inhoud):
    b = boot(lid().id, foto=png())
    sleutel = b.afbeelding.sleutel
    with pytest.raises(Regelfout):
        boten.foto_vervangen(b.id, inhoud, CLI)
    assert db.session.get(Boot, b.id).afbeelding.sleutel == sleutel
    assert db.session.scalar(select(func.count()).select_from(Afbeelding)) == 1


def test_decompressiebom_geweigerd(app, monkeypatch):
    monkeypatch.setattr(afbeeldingen, "MAX_PIXELS", 100)
    with pytest.raises(Regelfout):
        afbeeldingen.verwerk(png(20, 20))


def test_foto_vervangen_ruimt_oude_op(app):
    b = boot(lid().id, foto=png())
    oud = b.afbeelding.sleutel
    boten.foto_vervangen(b.id, png(50, 50), CLI)
    assert db.session.get(Boot, b.id).afbeelding.sleutel != oud
    assert afbeeldingen.op_sleutel(oud) is None
    assert acties()[-1] == "boot.foto_vervangen"


def test_boot_met_plaats_niet_te_verwijderen(app):
    p, b = plaats(), boot(lid().id, foto=png())
    toewijzing.toewijzen(p.id, b.id, CLI)
    with pytest.raises(Regelfout, match="Geef de plaats eerst vrij"):
        boten.boot_verwijderen(b.id, CLI)
    los = boot(lid("1002").id, foto=png())
    boten.boot_verwijderen(los.id, CLI)
    assert db.session.get(Boot, los.id) is None
    assert db.session.scalar(select(func.count()).select_from(Afbeelding)) == 1
    assert acties()[-1] == "boot.verwijderd"


# Toewijzen


def test_toewijzen_en_twee_boten_van_een_lid(app):
    anna = lid()
    p1, p2 = plaats("A/1/1"), plaats("A/1/2")
    b1, b2 = boot(anna.id), boot(anna.id, naam="Fuut")
    toewijzing.toewijzen(p1.id, b1.id, CLI)
    toewijzing.toewijzen(p2.id, b2.id, CLI)
    assert (p1.boot, p2.boot) == (b1, b2)
    regel = log.regels([f"plaats:{p1.id}"])[0]
    assert regel.actie == "plaats.toegewezen"
    assert regel.gegevens == {"plaats": "A/1/1", "boot": "Zeemeeuw"}


def test_clubboot_op_clubplaats(app):
    p = plaats(club=True)
    toewijzing.toewijzen(p.id, boot(None).id, CLI)
    assert p.boot.lid is None


@pytest.mark.parametrize("geval, melding", [
    ("bezet", "is al bezet"),
    ("al_plaats", "heeft al een plaats"),
    ("clubboot_op_ledenplaats", "hoort op een clubplaats"),
    ("ledenboot_op_clubplaats", "alleen voor clubboten"),
    ("verkeerde_soort", "niet geschikt voor een supboard"),
    ("oud_lid", "is oud-lid"),
    ("uit_bron", "is oud-lid"),
])
def test_toewijzen_geweigerd(app, geval, melding):
    p = plaats("A/1/1", club=geval == "ledenboot_op_clubplaats")
    gisteren = date.today() - timedelta(days=1)
    eigenaar = None if geval == "clubboot_op_ledenplaats" else lid(
        opzegdatum=gisteren if geval == "oud_lid" else None,
        uit_bron_op=gisteren if geval == "uit_bron" else None).id
    if geval in ("oud_lid", "uit_bron"):  # de boot bestond al voor de opzegging
        b = Boot(naam="Zeemeeuw", bootsoort_id=soort("Kajak"), lid_id=eigenaar)
        db.session.add(b)
        db.session.commit()
    else:
        b = boot(eigenaar, bootsoort="Supboard" if geval == "verkeerde_soort" else "Kajak")
    if geval == "bezet":
        toewijzing.toewijzen(p.id, boot(lid("1002").id, naam="Fuut").id, CLI)
    if geval == "al_plaats":
        toewijzing.toewijzen(plaats("A/1/2").id, b.id, CLI)
    voor = len(acties())
    with pytest.raises(Regelfout, match=melding):
        toewijzing.toewijzen(p.id, b.id, CLI)
    assert len(acties()) == voor
    assert db.session.get(Plaats, p.id).boot_id != b.id


def test_gelijktijdig_toewijzen_aan_dezelfde_plaats(app):
    """Twee databasesessies: de tweede wacht op de vergrendeling van de eerste en ziet daarna dat
    de plaats bezet is. Zonder FOR UPDATE zou ze de eerste toewijzing overschrijven."""
    p = plaats()
    b1, b2 = boot(lid().id), boot(lid("1002").id, naam="Fuut")
    fouten = []

    def tweede():
        with app.app_context():
            try:
                toewijzing.toewijzen(p.id, b2.id, CLI)
            except Regelfout as fout:
                fouten.append(str(fout))

    engine = create_engine(WEB)
    with engine.connect() as eerste:
        eerste.execute(text("SELECT id FROM plaats WHERE id = :p FOR UPDATE"), {"p": p.id})
        draad = threading.Thread(target=tweede)
        draad.start()
        draad.join(timeout=1)
        assert draad.is_alive()  # wacht op de vergrendeling
        eerste.execute(text("UPDATE plaats SET boot_id = :b WHERE id = :p"), {"b": b1.id, "p": p.id})
        eerste.commit()
    draad.join(timeout=5)
    engine.dispose()
    assert fouten == ["Plaats A/1/1 is al bezet."]
    db.session.expire_all()
    assert db.session.get(Plaats, p.id).boot_id == b1.id


def test_lid_met_opzegdatum_in_de_toekomst_krijgt_een_plaats(app):
    p = plaats()
    toewijzing.toewijzen(p.id, boot(lid(opzegdatum=date.today() + timedelta(days=30)).id).id, CLI)
    assert p.boot_id is not None


# Openbare leesfunctie


def test_openbaar_geeft_alleen_openbare_velden(app):
    p = plaats()
    assert indeling.openbaar(p.publieke_sleutel) == {
        "code": "A/1/1", "omschrijving": "", "vrij": True, "clubboot": False, "clubplaats": False, "boot": None, "foto": None,
        "eigenaar": None}
    b = boot(lid().id, foto=png())
    toewijzing.toewijzen(p.id, b.id, CLI)
    assert indeling.openbaar(p.publieke_sleutel) == {
        "code": "A/1/1", "omschrijving": "", "vrij": False, "clubboot": False, "clubplaats": False, "boot": "Zeemeeuw",
        "foto": b.afbeelding.sleutel, "eigenaar": "Anna de Vries"}
    assert indeling.openbaar("bestaatniet") is None


def test_toewijzen_pakt_de_plaats_niet_voor_de_boot(app):
    p = plaats()
    b = boot(lid().id)
    fouten = []

    def tweede():
        with app.app_context():
            try:
                toewijzing.toewijzen(p.id, b.id, CLI)
            except Regelfout as fout:
                fouten.append(str(fout))

    engine = create_engine(WEB)
    with engine.connect() as eerste:
        eerste.execute(text("SELECT id FROM boot WHERE id = :b FOR UPDATE"), {"b": b.id})
        draad = threading.Thread(target=tweede)
        draad.start()
        draad.join(timeout=1)
        assert draad.is_alive(), "toewijzen wacht niet op het bootslot"
        # Zoals boot_wijzigen (#39): na de boot de plaats. Houdt toewijzen de plaats al vast, dan faalt dit.
        eerste.execute(text("SELECT id FROM plaats WHERE id = :p FOR UPDATE NOWAIT"), {"p": p.id})
        eerste.commit()
    draad.join(timeout=5)
    engine.dispose()
    assert not fouten
    db.session.expire_all()
    assert db.session.get(Plaats, p.id).boot_id == b.id
