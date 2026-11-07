"""Overzichten (BLB-015 tot en met 019), Excel-export (BLB-017) en naam en logo
(BLB-027). Verschoven uit slice 2: BLB-011 criterium 2 en BLB-003 criterium 1."""

import io
import re
import time
from datetime import date, timedelta

import pytest
from openpyxl import load_workbook
from PIL import Image
from sqlalchemy import create_engine, func, select, update

from app import config
from app.config import UPLOAD_MAX
from app.domein import CLI, Regelfout, instellingen, toewijzing
from app.domein import vandaag as domein_vandaag
from app.models import Afbeelding, Instelling, Lid, Logregel, db
from app.web import huisstijl
from tests.unit.conftest import API
from tests.unit.hulp import lid, png
from tests.unit.test_indeling_en_toewijzing import boot, plaats, soort
from tests.unit.test_web_beheer import ingelogd  # noqa: F401  fixture

GISTEREN = date.today() - timedelta(days=1)


def opzeggen(lid_id, **velden):
    """Zoals de import, als de rol van de dienst api: de webrol mag leden alleen lezen."""
    engine = create_engine(API)
    with engine.begin() as c:
        c.execute(update(Lid).where(Lid.id == lid_id).values(**velden))
    engine.dispose()
    db.session.expire_all()


def loods():
    """Rek A met vier plaatsen: vrij (kajak, surfski), bezet, clubplaats en vrij (C11)."""
    vrij = plaats("A/1/1", ("Kajak", "Surfski"))
    bezet = plaats("A/1/2", ("Kajak",))
    club = plaats("A/1/3", ("Surfski",), club=True)
    c11 = plaats("A/1/4", ("C11",))
    anna = lid()
    toewijzing.toewijzen(bezet.id, boot(anna.id).id, CLI)
    return vrij, bezet, club, c11, anna


# Vrije plaatsen (BLB-015, BLB-011 criterium 2, BLB-003 criterium 1)


def test_vrije_plaatsen_zonder_bezet_en_clubplaats(app):
    vrij, _bezet, _club, c11, _anna = loods()
    from app.domein import indeling
    assert [p.code for p in indeling.vrije_plaatsen()] == [vrij.code, c11.code]
    assert [p.code for p in indeling.vrije_plaatsen(soort("Surfski"))] == ["A/1/1"]
    assert indeling.vrije_plaatsen(soort("Supboard")) == []


def test_vrije_plaatsen_filter_zonder_knop_met_script_en_focus(ingelogd):  # noqa: F811
    loods()
    zonder = ingelogd.get("/vrij").text
    zichtbaar = re.sub(r"<noscript>.*?</noscript>", "", zonder, flags=re.DOTALL)
    assert "<noscript><button" in zonder, "zonder script blijft de knop beschikbaar"
    assert "Filteren" not in zichtbaar, "knop Filteren buiten noscript"
    assert '<script src="/static/vrij.js"></script>' in zichtbaar, "script van de eigen site"
    assert "<script>" not in zichtbaar and "onchange" not in zichtbaar, "geen inline script"
    assert "autofocus" not in zonder, "autofocus zonder gekozen bootsoort"
    met = ingelogd.get(f"/vrij?bootsoort={soort('Surfski')}").text
    assert re.search(r'<select[^>]* id="bootsoort"[^>]* autofocus', met), "autofocus met gekozen bootsoort"


def test_vrije_plaatsen_scherm_met_filter_en_vrijgeven(ingelogd):  # noqa: F811
    _vrij, bezet, _club, _c11, _anna = loods()
    tekst = ingelogd.get("/vrij").text
    assert "A/1/1" in tekst and "Kajak, Surfski" in tekst
    assert ">A/1/2<" not in tekst and ">A/1/3<" not in tekst
    tekst = ingelogd.get(f"/vrij?bootsoort={soort('Surfski')}").text
    assert ">A/1/1<" in tekst and ">A/1/4<" not in tekst
    tekst = ingelogd.get(f"/vrij?bootsoort={soort('Supboard')}").text
    assert "Er zijn geen vrije plaatsen voor supboard." in tekst
    ingelogd.post(f"/plaatsen/{bezet.id}/vrijgeven")
    assert ">A/1/2<" in ingelogd.get("/vrij").text


# Indeling op het scherm (BLB-016)


def test_indeling_toont_status_boot_en_eigenaar(ingelogd):  # noqa: F811
    _vrij, bezet, club, _c11, _anna = loods()
    toewijzing.toewijzen(club.id, boot(None, "Surfski", "Clubski").id, CLI)
    tekst = ingelogd.get("/indeling").text
    assert f'href="/plaatsen/{bezet.id}">A/1/2</a>' in tekst
    assert "Zeemeeuw" in tekst and "Anna de Vries" in tekst
    assert '<span class="ds-tag">clubplaats</span>' in tekst and "Clubski" in tekst and "Botenloods" in tekst
    assert tekst.count('<span class="ds-tag">vrij</span>') == 2
    assert "Proefweg" not in tekst and "@example.org" not in tekst


# Lijst per lid (BLB-019)


def test_lid_met_boten_en_plaats(ingelogd):  # noqa: F811
    _vrij, bezet, _club, _c11, anna = loods()
    boot(anna.id, "Surfski", "Albatros")
    tekst = ingelogd.get(f"/leden/{anna.id}").text
    assert "Zeemeeuw" in tekst and f'href="/plaatsen/{bezet.id}">A/1/2</a>' in tekst
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
    p1 = plaats("B/1/1")
    p2, p3, p4 = (plaats(c) for c in ("B/1/2", "B/1/3", "B/1/4"))
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
    assert f'href="/plaatsen/{p2.id}">B/1/2</a>' in tekst and "Zegt Later Op" not in tekst


def test_geen_plaatsen_van_oud_leden(ingelogd):  # noqa: F811
    loods()
    assert "Er zijn geen plaatsen van opgezegde leden." in ingelogd.get("/opgezegd").text


# Boten van leden die gaan opzeggen (BLB-041)


def test_boten_van_leden_die_gaan_opzeggen_vroegste_eerst(ingelogd):  # noqa: F811
    """BLB-041 criteria 2 tot en met 4."""
    p1 = plaats("C/1/1")
    p2, p3 = (plaats(c) for c in ("C/1/2", "C/1/3"))
    namen = ("Zegt Laat Op", "Zegt Vroeg Op", "Al Opgezegd", "Zonder Plaats", "Blijft Lid")
    laat, vroeg, al, zonder, _blijft = (lid(str(n), naam) for n, naam in enumerate(namen))
    for p, eigenaar in ((p1, laat), (p2, vroeg), (p3, al)):
        toewijzing.toewijzen(p.id, boot(eigenaar.id, naam=f"Boot {eigenaar.naam}").id, CLI)
    boot(zonder.id, naam="Boot zonder plaats")
    vandaag = domein_vandaag()  # tijdzone van de installatie, niet UTC van de container
    opzeggen(laat.id, opzegdatum=vandaag + timedelta(days=60))
    opzeggen(vroeg.id, opzegdatum=vandaag + timedelta(days=1))
    opzeggen(al.id, opzegdatum=vandaag)  # vandaag opgezegd: oud-lid, staat bij BLB-018
    opzeggen(zonder.id, opzegdatum=vandaag + timedelta(days=5))
    tekst = ingelogd.get("/opzeggend").text
    assert tekst.index("Zegt Vroeg Op") < tekst.index("Zegt Laat Op")
    assert "Boot Zegt Vroeg Op" in tekst
    assert f'href="/plaatsen/{p2.id}">C/1/2</a>' in tekst
    assert (vandaag + timedelta(days=1)).strftime("%d-%m-%Y") in tekst
    for weg in ("Al Opgezegd", "Zonder Plaats", "Blijft Lid"):
        assert weg not in tekst
    assert "Al Opgezegd" in ingelogd.get("/opgezegd").text


@pytest.mark.parametrize("dagen", [-1, 30], ids=["opgezegd", "opzeggend"])
def test_zelfde_datum_op_rek_verdieping_vak(app, dagen):
    """Issue #81: rek A vóór B ondanks de hogere verdieping, en verdieping vóór vak."""
    from app.domein import indeling
    plaats("A/1/1")  # rek A eerst aangemaakt, dus eerst in de volgorde
    plaats("B/1/1")
    codes = ("A/2/1", "B/2/1", "B/1/2")
    for n, code in enumerate(codes):
        eigenaar = lid(str(n), f"Lid {n}")
        toewijzing.toewijzen(plaats(code).id, boot(eigenaar.id).id, CLI)
        opzeggen(eigenaar.id, opzegdatum=domein_vandaag() + timedelta(days=dagen))
    rijen = (indeling.plaatsen_van_oud_leden() if dagen < 0
             else indeling.plaatsen_van_opzeggende_leden())
    plaatsen = [r[1] if dagen < 0 else r for r in rijen]
    assert [f"{p.rek.naam}/{p.verdieping}/{p.vak}" for p in plaatsen] == [
        "A/2/1", "B/1/2", "B/2/1"]


def test_geen_boten_van_leden_die_gaan_opzeggen(ingelogd):  # noqa: F811
    """BLB-041 criterium 5."""
    loods()
    tekst = ingelogd.get("/opzeggend").text
    assert "Er zijn geen boten van leden die gaan opzeggen." in tekst
    assert 'href="/opzeggend"' in tekst  # in het menu


# Excel-export (BLB-017)


def test_export_kolommen_en_geen_contactgegevens(ingelogd):  # noqa: F811
    _vrij, _bezet, club, _c11, _anna = loods()
    toewijzing.toewijzen(club.id, boot(None, "Surfski", "Clubski").id, CLI)
    plaats("A/1/5", ("Kajak", "Canadese kano"), club=True)  # clubplaats zonder boot
    r = ingelogd.get("/indeling.xlsx")
    assert r.status_code == 200 and "attachment" in r.headers["Content-Disposition"]
    blad = load_workbook(io.BytesIO(r.data)).active
    rijen = [tuple(c.value for c in rij) for rij in blad.iter_rows()]
    assert rijen == [
        ("Rek", "Code", "Status", "Bootsoort", "Bootnaam", "Eigenaar", "Lidnummer"),
        ("A", "A/1/1", "vrij", "(geschikt voor Kajak, Surfski)", None, None, None),
        ("A", "A/1/2", "bezet", "Kajak", "Zeemeeuw", "Anna de Vries", "1001"),
        ("A", "A/1/3", "clubplaats", "Surfski", "Clubski", "Botenloods", None),
        ("A", "A/1/4", "vrij", "(geschikt voor C11)", None, None, None),
        ("A", "A/1/5", "clubplaats", "(geschikt voor Kajak, Canadese kano)", None, None, None)]
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


# Naam en logo (BLB-027); de kleuren vervielen met issue #150


def test_neutrale_standaard_zonder_instellingen_en_zonder_logo(app, client):
    assert app.config["LOGO_BESTAND"] == "/huisstijl/logo.png"  # bestaat niet in de testcontainer
    assert app.extensions["logo"] is None
    assert instellingen.huidig() == instellingen.STANDAARD
    tekst = client.get("/inloggen").text
    assert "Inloggen · Botenloods</title>" in tekst and 'class="bl-logo"' not in tekst


def test_pagina_laadt_de_dajaks_basis_en_geen_huisstijl(client):
    """Laadvolgorde van de basis (#150): tokens, ds-, dj-, product. Geen stylesheet met kleuren."""
    tekst = client.get("/inloggen").text
    volgorde = ["ds/tokens/dajaks.css", "ds/ds-components.css", "dj/dj-components.css", "stijl.css"]
    assert [tekst.index(f"/static/{css}") for css in volgorde] == sorted(
        tekst.index(f"/static/{css}") for css in volgorde)
    assert "huisstijl.css" not in tekst
    assert client.get("/huisstijl.css").status_code == 404


def test_opslaan_met_log_en_overal_zichtbaar(app, ingelogd):  # noqa: F811
    p = plaats()
    r = ingelogd.post("/instellingen", data={"naam": "KV De Fuut"}, follow_redirects=True)
    assert "De instellingen zijn opgeslagen." in r.text
    assert "instelling.gewijzigd" in ingelogd.get("/log/techniek").text  # BLB-043
    regel = db.session.scalar(select(Logregel).where(Logregel.actie == "instelling.gewijzigd"))
    assert regel.gegevens == {"naam": ["Botenloods", "KV De Fuut"]}
    client = app.test_client()  # bezoeker
    assert "KV De Fuut" in client.get(f"/p/{p.publieke_sleutel}").text


def test_geen_kleurkiezers_en_kleurvelden_worden_genegeerd(app, ingelogd):  # noqa: F811
    assert 'type="color"' not in ingelogd.get("/instellingen").text
    ingelogd.post("/instellingen", data={"naam": "KV", "kleur_primair": "#1a4d2e",
                                         "kleur_secundair": "#333333"})
    assert db.session.scalars(select(Instelling.sleutel)).all() == ["naam"]


@pytest.mark.parametrize("naam", ["", "   ", "x" * 101], ids=["leeg", "spaties", "te lang"])
def test_ongeldige_naam_geweigerd(app, naam):
    with pytest.raises(Regelfout):
        instellingen.opslaan(naam, CLI)
    assert db.session.scalar(select(func.count()).select_from(Instelling)) == 0


X = "<b>x</b>"
GEESCAPET = "&lt;b&gt;x&lt;/b&gt;"


def test_melding_en_schermen_escapen_invoer(app, ingelogd):  # noqa: F811
    """Issue #150: de macro meldingblok en de gewijzigde sjablonen tonen invoer geëscapet."""
    from flask import render_template_string
    html = render_template_string('{% from "_melding.html" import meldingblok %}'
                                  "{% call meldingblok('danger') %}{{ x }}{% endcall %}", x=X)
    assert GEESCAPET in html and X not in html
    with ingelogd.session_transaction() as s:  # een flashbericht, zoals base.html het toont
        s["_flashes"] = [("fout", X)]
    tekst = ingelogd.get("/").text
    assert GEESCAPET in tekst and X not in tekst
    p = plaats()
    b = boot(lid(naam=X).id, naam=X)
    for pad in (f"/boten/{b.id}", f"/plaatsen/{p.id}", "/boten", "/leden", "/instellingen"):
        tekst = ingelogd.get(pad).text
        assert X not in tekst, pad
    assert GEESCAPET in ingelogd.get(f"/boten/{b.id}").text


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
        assert f'class="bl-logo" src="/logo/{kenmerk}"' in client.get(pad).text
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
    assert 'class="bl-logo"' not in tekst and "/logo/" not in tekst


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
    r = ingelogd.post("/instellingen", data={"naam": "Overgenomen"})
    assert r.status_code == 302 and r.location.endswith("/inloggen")
    assert db.session.scalar(select(func.count()).select_from(Instelling)) == 0


@pytest.mark.parametrize("pad", ["/instellingen", "/vrij", "/opgezegd", "/leden/1"])
def test_schermen_vragen_inloggen(client, pad):
    r = client.get(pad)
    assert r.status_code == 302 and r.location.endswith("/inloggen")


def test_bezoeker_wijzigt_geen_instellingen(client):
    r = client.post("/instellingen", data={"naam": "X"})
    assert r.status_code == 302 and r.location.endswith("/inloggen")
    assert db.session.scalar(select(func.count()).select_from(Instelling)) == 0
