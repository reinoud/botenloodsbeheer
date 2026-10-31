"""Overzichten (BLB-015 tot en met 019), Excel-export (BLB-017) en naam, kleuren en logo
(BLB-027). Verschoven uit slice 2: BLB-011 criterium 2 en BLB-003 criterium 1."""

import io
import time
from datetime import date, timedelta

import pytest
from openpyxl import load_workbook
from PIL import Image
from sqlalchemy import create_engine, func, select, update

from app import config
from app.config import UPLOAD_MAX
from app.domein import CLI, Regelfout, instellingen, toewijzing
from app.models import Afbeelding, Instelling, Lid, Logregel, db
from app.web import huisstijl
from tests.unit.conftest import TAKEN
from tests.unit.hulp import lid, png
from tests.unit.test_indeling_en_toewijzing import boot, plaats, soort
from tests.unit.test_web_beheer import ingelogd  # noqa: F401  fixture

GISTEREN = date.today() - timedelta(days=1)


def opzeggen(lid_id, **velden):
    """Zoals de synchronisatie, als de taakrol: de webrol mag leden alleen lezen."""
    engine = create_engine(TAKEN)
    with engine.begin() as c:
        c.execute(update(Lid).where(Lid.id == lid_id).values(**velden))
    engine.dispose()
    db.session.expire_all()


def loods():
    """Rek A met vier plaatsen: vrij (kajak, surfski), bezet, clubplaats en vrij (C11)."""
    vrij = plaats("A01", ("Kajak", "Surfski"))
    rek = vrij.rek
    bezet = plaats("A02", ("Kajak",), rek=rek)
    club = plaats("A03", ("Surfski",), club=True, rek=rek)
    c11 = plaats("A04", ("C11",), rek=rek)
    anna = lid()
    toewijzing.toewijzen(bezet.id, boot(anna.id).id, CLI)
    return vrij, bezet, club, c11, anna


# Vrije plaatsen (BLB-015, BLB-011 criterium 2, BLB-003 criterium 1)


def test_vrije_plaatsen_zonder_bezet_en_clubplaats(app):
    vrij, _bezet, _club, c11, _anna = loods()
    from app.domein import indeling
    assert [p.code for p in indeling.vrije_plaatsen()] == [vrij.code, c11.code]
    assert [p.code for p in indeling.vrije_plaatsen(soort("Surfski"))] == ["A01"]
    assert indeling.vrije_plaatsen(soort("Supboard")) == []


def test_vrije_plaatsen_scherm_met_filter_en_vrijgeven(ingelogd):  # noqa: F811
    _vrij, bezet, _club, _c11, _anna = loods()
    tekst = ingelogd.get("/vrij").text
    assert "A01" in tekst and "Kajak, Surfski" in tekst and "Rek A" in tekst
    assert ">A02<" not in tekst and ">A03<" not in tekst
    tekst = ingelogd.get(f"/vrij?bootsoort={soort('Surfski')}").text
    assert ">A01<" in tekst and ">A04<" not in tekst
    tekst = ingelogd.get(f"/vrij?bootsoort={soort('Supboard')}").text
    assert "Er zijn geen vrije plaatsen voor supboard." in tekst
    ingelogd.post(f"/plaatsen/{bezet.id}/vrijgeven")
    assert ">A02<" in ingelogd.get("/vrij").text


# Indeling op het scherm (BLB-016)


def test_indeling_toont_status_boot_en_eigenaar(ingelogd):  # noqa: F811
    _vrij, bezet, club, _c11, _anna = loods()
    toewijzing.toewijzen(club.id, boot(None, "Surfski", "Clubski").id, CLI)
    tekst = ingelogd.get("/indeling").text
    assert f'href="/plaatsen/{bezet.id}">A02</a>' in tekst
    assert "Zeemeeuw" in tekst and "Anna de Vries" in tekst
    assert "status-clubplaats" in tekst and "Clubski" in tekst and "Botenloods" in tekst
    assert tekst.count('class="status-vrij"') == 2
    assert "Proefweg" not in tekst and "@example.org" not in tekst


# Lijst per lid (BLB-019)


def test_lid_met_boten_en_plaats(ingelogd):  # noqa: F811
    _vrij, bezet, _club, _c11, anna = loods()
    boot(anna.id, "Surfski", "Albatros")
    tekst = ingelogd.get(f"/leden/{anna.id}").text
    assert "Zeemeeuw" in tekst and f'href="/plaatsen/{bezet.id}">A02</a>' in tekst
    assert "Albatros" in tekst and "Geen plaats" in tekst and "Surfski" in tekst
    assert "Proefweg" not in tekst and "06-0000" not in tekst and "@example.org" not in tekst
    assert ingelogd.get("/leden/999").status_code == 404


def test_leden_zoeken_op_naam_of_lidnummer(ingelogd):  # noqa: F811
    lid("1001", "Anna de Vries")
    lid("2002", "Bert_Jansen")
    lid("3003", "Carla 100% Smit")
    tekst = ingelogd.get("/leden?zoek=vries").text
    assert "Anna de Vries" in tekst and "Bert_Jansen" not in tekst
    tekst = ingelogd.get("/leden?zoek=200").text
    assert "Bert_Jansen" in tekst and "Anna de Vries" not in tekst
    # % en _ zijn gewone tekens, geen jokers.
    assert "Carla" in ingelogd.get("/leden?zoek=0%25").text
    assert "Anna" not in ingelogd.get("/leden?zoek=0%25").text
    assert "Geen leden gevonden." in ingelogd.get("/leden?zoek=a_d").text  # geen "a d"
    assert "Bert_Jansen" in ingelogd.get("/leden?zoek=T_j").text


# Plaatsen van opgezegde leden (BLB-018)


def test_plaatsen_van_oud_leden_oudste_eerst(ingelogd):  # noqa: F811
    from app.domein import indeling
    p1 = plaats("B01")
    p2, p3, p4 = (plaats(c, rek=p1.rek) for c in ("B02", "B03", "B04"))
    namen = ("Recent Opgezegd", "Lang Geleden", "Uit De Bron", "Zegt Later Op")
    eigenaren = [lid(str(n), naam) for n, naam in enumerate(namen)]
    for p, eigenaar in zip((p1, p2, p3, p4), eigenaren):
        toewijzing.toewijzen(p.id, boot(eigenaar.id, naam=f"Boot {eigenaar.naam}").id, CLI)
    recent, oud, weg, later = eigenaren
    opzeggen(recent.id, opzegdatum=GISTEREN)
    opzeggen(oud.id, opzegdatum=GISTEREN - timedelta(days=300))
    opzeggen(weg.id, uit_bron_op=GISTEREN - timedelta(days=10))
    opzeggen(later.id, opzegdatum=date.today() + timedelta(days=30))
    rijen = indeling.plaatsen_van_oud_leden()
    assert [(d, p.boot.lid.naam) for d, p in rijen] == [
        (GISTEREN - timedelta(days=300), "Lang Geleden"),
        (GISTEREN - timedelta(days=10), "Uit De Bron"),
        (GISTEREN, "Recent Opgezegd")]
    tekst = ingelogd.get("/opgezegd").text
    assert tekst.index("Lang Geleden") < tekst.index("Uit De Bron") < tekst.index("Recent")
    assert f'href="/plaatsen/{p2.id}">B02</a>' in tekst and "Zegt Later Op" not in tekst


def test_geen_plaatsen_van_oud_leden(ingelogd):  # noqa: F811
    loods()
    assert "Er zijn geen plaatsen van opgezegde leden." in ingelogd.get("/opgezegd").text


# Excel-export (BLB-017)


def test_export_kolommen_en_geen_contactgegevens(ingelogd):  # noqa: F811
    vrij, _bezet, club, _c11, _anna = loods()
    toewijzing.toewijzen(club.id, boot(None, "Surfski", "Clubski").id, CLI)
    plaats("A05", ("Kajak", "Canadese kano"), club=True, rek=vrij.rek)  # clubplaats zonder boot
    r = ingelogd.get("/indeling.xlsx")
    assert r.status_code == 200 and "attachment" in r.headers["Content-Disposition"]
    blad = load_workbook(io.BytesIO(r.data)).active
    rijen = [tuple(c.value for c in rij) for rij in blad.iter_rows()]
    assert rijen == [
        ("Rek", "Code", "Status", "Bootsoort", "Bootnaam", "Eigenaar", "Lidnummer"),
        ("Rek A", "A01", "vrij", "(geschikt voor Kajak, Surfski)", None, None, None),
        ("Rek A", "A02", "bezet", "Kajak", "Zeemeeuw", "Anna de Vries", "1001"),
        ("Rek A", "A03", "clubplaats", "Surfski", "Clubski", "Botenloods", None),
        ("Rek A", "A04", "vrij", "(geschikt voor C11)", None, None, None),
        ("Rek A", "A05", "clubplaats", "(geschikt voor Kajak, Canadese kano)", None, None, None)]
    inhoud = str(rijen)
    for verboden in ("Proefweg", "06-0000", "@example.org"):
        assert verboden not in inhoud
    assert not blad._images


def test_export_maakt_geen_formule_van_een_naam(ingelogd):  # noqa: F811
    p = plaats()
    toewijzing.toewijzen(p.id, boot(lid("9", '=HYPERLINK("http://example.org","x")').id).id, CLI)
    blad = load_workbook(io.BytesIO(ingelogd.get("/indeling.xlsx").data)).active
    cel = blad["F2"]
    assert cel.value.startswith("=HYPERLINK") and cel.data_type == "s"


def test_export_vraagt_inloggen(client):
    r = client.get("/indeling.xlsx")
    assert r.status_code == 302 and r.location.endswith("/inloggen")


# Naam, kleuren en logo (BLB-027)


def test_neutrale_standaard_zonder_instellingen_en_zonder_logo(app, client):
    assert app.config["LOGO_BESTAND"] == "/huisstijl/logo.png"  # bestaat niet in de testcontainer
    assert app.extensions["logo"] is None
    assert instellingen.huidig() == instellingen.STANDAARD
    assert "--kleur-primair: #3f6fb5" in client.get("/huisstijl.css").text
    tekst = client.get("/inloggen").text
    assert "Inloggen · Botenloods</title>" in tekst and 'class="logo"' not in tekst


def test_opslaan_met_log_en_overal_zichtbaar(app, ingelogd):  # noqa: F811
    p = plaats()
    r = ingelogd.post("/instellingen", data={"naam": "KV De Fuut", "kleur_primair": "#1A4D2E",
                                             "kleur_secundair": "#333333"}, follow_redirects=True)
    assert "De instellingen zijn opgeslagen." in r.text and "slecht leesbaar" not in r.text
    assert "instelling.gewijzigd" in r.text
    regel = db.session.scalar(select(Logregel).where(Logregel.actie == "instelling.gewijzigd"))
    assert regel.gegevens["kleur_primair"] == ["#3f6fb5", "#1a4d2e"]
    assert regel.gegevens["naam"] == ["Botenloods", "KV De Fuut"]
    client = app.test_client()  # bezoeker
    openbaar = client.get(f"/p/{p.publieke_sleutel}")
    assert "KV De Fuut" in openbaar.text and "/huisstijl.css" in openbaar.text
    css = client.get("/huisstijl.css")
    assert "--kleur-primair: #1a4d2e" in css.text and css.mimetype == "text/css"
    assert "Set-Cookie" not in css.headers


def test_slecht_contrast_geeft_waarschuwing_maar_slaat_op(app):
    waarschuwingen = instellingen.opslaan("KV", "#ffff00", "#eeeeee", CLI)
    assert len(waarschuwingen) == 2 and "kopbalk" in waarschuwingen[0]
    assert instellingen.huidig()["kleur_primair"] == "#ffff00"
    assert instellingen.opslaan("KV", "#000000", "#000000", CLI) == []


def test_contrast_volgens_wcag():
    assert instellingen.contrast("#000000", "#ffffff") == pytest.approx(21)
    assert instellingen.contrast("#777777", "#ffffff") == pytest.approx(4.48, abs=0.01)


@pytest.mark.parametrize("naam, kleur", [("", "#123456"), ("x" * 101, "#123456"),
                                         ("KV", "red"), ("KV", "#12345"),
                                         ("KV", "#123456;}body{x")])
def test_ongeldige_naam_of_kleur_geweigerd(app, naam, kleur):
    with pytest.raises(Regelfout):
        instellingen.opslaan(naam, kleur, "#000000", CLI)
    assert db.session.scalar(select(func.count()).select_from(Instelling)) == 0


def test_ongeldige_kleur_in_database_wordt_standaard(app):
    db.session.add(Instelling(sleutel="kleur_primair", waarde="red;}*{x"))
    db.session.commit()
    assert instellingen.huidig()["kleur_primair"] == "#3f6fb5"


def logo_uit_installatie(app, tmp_path, inhoud):
    """Zoals web bij het starten, met LOGO_BESTAND naar een bestand in de installatie."""
    pad = tmp_path / "logo.png"
    pad.write_bytes(inhoud)
    app.config["LOGO_BESTAND"] = str(pad)
    huisstijl.logo_laden(app)
    return app.extensions["logo"]


def test_logo_uit_installatie_op_alle_paginas_zonder_metadata(app, client, tmp_path, caplog):
    exif = Image.Exif()
    exif[0x8825] = {2: (52.0, 22.0, 1.0)}  # GPS-gegevens
    kenmerk, _ = logo_uit_installatie(app, tmp_path, png(1200, 300, exif=exif.tobytes(), icc=b"bron-kleurprofiel"))
    assert "Logo geladen" in caplog.text
    p = plaats()
    for pad in ("/inloggen", f"/p/{p.publieke_sleutel}"):
        assert f'src="/logo/{kenmerk}"' in client.get(pad).text
    r = client.get(f"/logo/{kenmerk}")
    assert r.status_code == 200 and r.mimetype == "image/png"
    assert r.headers["Cache-Control"] == "public, max-age=31536000, immutable"
    assert r.headers["X-Content-Type-Options"] == "nosniff" and "Set-Cookie" not in r.headers
    with Image.open(io.BytesIO(r.data)) as img:
        assert img.format == "PNG" and img.size == (800, 200)
        assert not img.getexif() and "exif" not in img.info and "icc_profile" not in img.info
    assert client.get("/logo/0123456789abcdef").status_code == 404
    # Geen mutatie: geen logregel over de huisstijl en niets in de database.
    acties = db.session.scalars(select(Logregel.actie)).all()
    assert acties and not [a for a in acties if a.startswith("instelling")]
    assert db.session.scalar(select(func.count()).select_from(Afbeelding)) == 0


def test_nieuw_logo_na_herstart_krijgt_nieuwe_url(app, tmp_path):
    eerste, _ = logo_uit_installatie(app, tmp_path, png())
    tweede, _ = logo_uit_installatie(app, tmp_path, png(20, 20))
    assert eerste != tweede


@pytest.mark.parametrize("inhoud", [
    None,  # bestand ontbreekt
    b"geen afbeelding",
    b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
    png(formaat="GIF"),
    png() + b"0" * UPLOAD_MAX],  # geldige PNG, maar groter dan 10 MB
    ids=["ontbreekt", "tekst", "svg", "gif", "te-groot"])
def test_ontbrekend_of_ongeldig_logo_toont_alleen_de_naam(app, client, tmp_path, caplog, inhoud):
    if inhoud is None:
        app.config["LOGO_BESTAND"] = str(tmp_path / "bestaat-niet.png")
        huisstijl.logo_laden(app)
    else:
        logo_uit_installatie(app, tmp_path, inhoud)
    assert app.extensions["logo"] is None
    assert "alleen de naam" in caplog.text and caplog.records[-1].levelname == "WARNING"
    tekst = client.get("/inloggen").text
    assert 'class="logo"' not in tekst and "/logo/" not in tekst


def test_worker_leest_geen_logo(monkeypatch):
    monkeypatch.setenv("DIENST", "worker")
    assert config.laad()["LOGO_BESTAND"] is None


def test_geen_logo_uploaden_of_verwijderen(ingelogd):  # noqa: F811
    tekst = ingelogd.get("/instellingen").text
    assert 'type="file"' not in tekst and "Logo opslaan" not in tekst
    assert "staat in de installatie" in tekst
    assert ingelogd.post("/instellingen/logo", data={"logo": (io.BytesIO(png()), "l.png")}
                         ).status_code == 404


def test_recente_inlog_vereist(ingelogd):  # noqa: F811
    with ingelogd.session_transaction() as s:
        s["ingelogd_op"] = int(time.time()) - 601
    r = ingelogd.post("/instellingen", data={"naam": "Overgenomen", "kleur_primair": "#000000",
                                             "kleur_secundair": "#000000"})
    assert r.status_code == 302 and r.location.endswith("/inloggen")
    assert db.session.scalar(select(func.count()).select_from(Instelling)) == 0


@pytest.mark.parametrize("pad", ["/instellingen", "/vrij", "/opgezegd", "/leden/1"])
def test_schermen_vragen_inloggen(client, pad):
    r = client.get(pad)
    assert r.status_code == 302 and r.location.endswith("/inloggen")


def test_bezoeker_wijzigt_geen_instellingen(client):
    r = client.post("/instellingen", data={"naam": "X", "kleur_primair": "#000000",
                                           "kleur_secundair": "#000000"})
    assert r.status_code == 302 and r.location.endswith("/inloggen")
    assert db.session.scalar(select(func.count()).select_from(Instelling)) == 0
