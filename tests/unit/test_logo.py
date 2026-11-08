"""Logo uploaden, vervangen en verwijderen op Instellingen (issue #186, ADR-008, designsystem gh#35,
BV-65). Het logo staat in de database; elke worker van web ziet dezelfde stand."""

import io
import re
import time

import pytest
from PIL import Image
from sqlalchemy import func, select

from app import create_app
from app.config import UPLOAD_MAX
from app.domein import CLI, indeling, instellingen
from app.models import Afbeelding, Instelling, Logregel, db
from tests.unit.conftest import WEB
from tests.unit.hulp import logo_zetten, png
from tests.unit.test_indeling_en_toewijzing import plaats
from tests.unit.test_web_beheer import bezette_plaats, ingelogd  # noqa: F401  fixture

MELDING = "Dit bestand is geen geldige afbeelding in JPEG, PNG of WebP. De vorige blijft staan."


def uploaden(client, inhoud, naam="logo.png", **vraag):
    return client.post("/instellingen/logo", data={"logo": (io.BytesIO(inhoud), naam)}, **vraag)


def aantal_logos():
    return db.session.scalar(select(func.count()).select_from(Afbeelding)
                             .where(Afbeelding.soort == "logo"))


def acties():
    """De logacties over het logo, oudste eerst."""
    return db.session.scalars(select(Logregel.actie).where(Logregel.actie.like("instelling.logo%"))
                              .order_by(Logregel.id)).all()


def test_create_app_start_zonder_logo_bestand_en_negeert_de_oude_variabele(monkeypatch):
    """De variabele LOGO_BESTAND bestaat niet meer: ook met een waarde start web gewoon."""
    monkeypatch.setenv("LOGO_BESTAND", "/bestaat/niet.png")
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": WEB})
    assert "LOGO_BESTAND" not in app.config and "logo" not in app.extensions
    assert app.test_client().get("/inloggen").status_code == 200


def test_uploaden_toont_het_logo_overal_zonder_metadata_en_logt_zonder_inhoud(app, ingelogd):  # noqa: F811
    exif = Image.Exif()
    exif[0x8825] = {2: (52.0, 22.0, 1.0)}  # GPS-gegevens
    r = uploaden(ingelogd, png(1200, 300, exif=exif.tobytes(), icc=b"bron-kleurprofiel"),
                 follow_redirects=True)
    assert "Het logo is opgeslagen." in r.text
    kenmerk = instellingen.logo()
    assert re.fullmatch(r"[\w-]{16}", kenmerk) and aantal_logos() == 1
    p = bezette_plaats()
    bezoeker = app.test_client()
    for client, pad in ((bezoeker, "/inloggen"), (bezoeker, f"/p/{p.publieke_sleutel}"),
                        (ingelogd, "/rekoverzicht"), (ingelogd, f"/kaartjes/print?plaats={p.id}")):
        assert f'src="/logo/{kenmerk}"' in client.get(pad).text, pad
    assert f'<img class="bl-foto" src="/logo/{kenmerk}" alt="Huidig logo">' in ingelogd.get("/instellingen").text
    r = bezoeker.get(f"/logo/{kenmerk}")
    assert r.status_code == 200 and r.mimetype == "image/png"
    assert r.headers["Cache-Control"] == "public, max-age=31536000, immutable"
    assert r.headers["X-Content-Type-Options"] == "nosniff" and "Set-Cookie" not in r.headers
    with Image.open(io.BytesIO(r.data)) as img:
        assert img.format == "PNG" and img.size == (800, 200)
        assert not img.getexif() and "exif" not in img.info and "icc_profile" not in img.info
    regel = db.session.scalar(select(Logregel).where(Logregel.actie.like("instelling.logo%")))
    assert regel.actie == "instelling.logo_toegevoegd" and regel.verwijzingen == ["instelling:huisstijl"]
    assert regel.gegevens == {"breedte": 800, "hoogte": 200}  # geen inhoud, geen bestandsnaam
    assert "instelling.logo_toegevoegd" in ingelogd.get("/log/techniek").text
    assert "instelling.logo" not in ingelogd.get("/log").text  # geen bootmutatie


def test_vervangen_geeft_een_nieuw_kenmerk_en_het_oude_geeft_404(app, ingelogd):  # noqa: F811
    oud = logo_zetten(png(40, 30))
    uploaden(ingelogd, png(20, 20))
    nieuw = instellingen.logo()
    assert nieuw != oud and aantal_logos() == 1
    assert ingelogd.get(f"/logo/{nieuw}").status_code == 200
    assert ingelogd.get(f"/logo/{oud}").status_code == 404
    assert acties() == ["instelling.logo_toegevoegd", "instelling.logo_vervangen"]
    assert f'src="/logo/{nieuw}"' in app.test_client().get("/inloggen").text


def test_verwijderen_laat_alleen_de_naam_en_logt_zonder_inhoud(app, ingelogd):  # noqa: F811
    kenmerk = logo_zetten()
    r = ingelogd.post("/instellingen/logo/verwijderen", follow_redirects=True)
    assert "Het logo is verwijderd." in r.text
    assert instellingen.logo() is None and aantal_logos() == 0
    assert ingelogd.get(f"/logo/{kenmerk}").status_code == 404
    tekst = app.test_client().get("/inloggen").text
    assert 'class="bl-logo"' not in tekst and "/logo/" not in tekst
    regel = db.session.scalar(select(Logregel).where(Logregel.actie == "instelling.logo_verwijderd"))
    assert regel.gegevens == {} and regel.verwijzingen == ["instelling:huisstijl"]
    # Het scherm biedt het verwijderen niet meer aan; opslaan blijft kunnen.
    tekst = ingelogd.get("/instellingen").text
    assert "Logo verwijderen" not in tekst and "Logo opslaan" in tekst and "Er is geen logo." in tekst


def test_verwijderen_zonder_logo_geeft_een_melding_en_geen_logregel(ingelogd):  # noqa: F811
    r = ingelogd.post("/instellingen/logo/verwijderen", follow_redirects=True)
    assert "Er is geen logo om te verwijderen." in r.text
    assert acties() == []


def test_scherm_toont_het_blok_met_upload_en_verwijderknop(ingelogd):  # noqa: F811
    tekst = ingelogd.get("/instellingen").text
    assert re.search(r'<details class="dj-disclosure">\s*<summary>Logo</summary>', tekst)
    assert 'enctype="multipart/form-data"' in tekst and 'name="logo" type="file"' in tekst
    assert "Logo verwijderen" not in tekst  # geen logo, dus geen knop
    logo_zetten()
    assert "Logo verwijderen" in ingelogd.get("/instellingen").text
    assert re.search(r'<details class="dj-disclosure" open>\s*<summary>Logo</summary>',
                     ingelogd.get("/instellingen?open=logo").text)


@pytest.mark.parametrize("inhoud", [
    b"geen afbeelding",
    b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
    png(formaat="GIF"),
], ids=["tekst", "svg", "gif"])
def test_ongeldig_bestand_geeft_een_melding_en_het_vorige_logo_blijft(ingelogd, inhoud):  # noqa: F811
    vorig = logo_zetten()
    r = uploaden(ingelogd, inhoud, naam="<b>geheim</b>.png")
    assert r.location == "/instellingen?open=logo"
    r = ingelogd.get(r.location)
    assert r.text.count('role="alert"') == 1 and MELDING in r.text
    assert "geheim" not in r.text and "<b>geheim" not in r.text  # de bestandsnaam komt nergens terug
    assert re.search(r'<details class="dj-disclosure" open>\s*<summary>Logo</summary>', r.text)
    assert instellingen.logo() == vorig and aantal_logos() == 1
    assert acties() == ["instelling.logo_toegevoegd"]


def test_geen_bestand_gekozen_geeft_een_melding(ingelogd):  # noqa: F811
    vorig = logo_zetten()
    r = ingelogd.post("/instellingen/logo", data={"logo": (io.BytesIO(b""), "")}, follow_redirects=True)
    assert "Kies een logo." in r.text and 'summary>Logo</summary>' in r.text
    r = ingelogd.post("/instellingen/logo", data={}, follow_redirects=True)
    assert "Kies een logo." in r.text and instellingen.logo() == vorig


def test_bestand_boven_de_grens_wordt_geweigerd_en_het_vorige_logo_blijft(ingelogd, app):  # noqa: F811
    # Grens van het framework: MAX_CONTENT_LENGTH weigert vóór de route (en vóór CSRFProtect).
    vorig = logo_zetten()
    assert app.config["MAX_CONTENT_LENGTH"] == UPLOAD_MAX
    r = uploaden(ingelogd, png() + b"0" * UPLOAD_MAX)
    assert r.status_code == 413 and instellingen.logo() == vorig


def test_bestand_net_onder_de_grens_wordt_verwerkt(ingelogd):  # noqa: F811
    # Beide kanten van de grens: dit bestand is bijna 10 MB en geldig; het ene byte erboven geeft 413.
    inhoud = png() + b"0" * (UPLOAD_MAX - len(png()) - 2048)
    assert uploaden(ingelogd, inhoud).status_code == 302 and instellingen.logo() is not None


@pytest.mark.parametrize("pad", ["/instellingen/logo", "/instellingen/logo/verwijderen"])
def test_opslaan_en_verwijderen_vragen_een_recente_inlog(ingelogd, pad):  # noqa: F811
    vorig = logo_zetten()
    with ingelogd.session_transaction() as s:
        s["ingelogd_op"] = int(time.time()) - 601
    r = ingelogd.post(pad, data={"logo": (io.BytesIO(png(20, 20)), "l.png")})
    assert r.status_code == 302 and r.location.endswith("/inloggen")
    assert instellingen.logo() == vorig and acties() == ["instelling.logo_toegevoegd"]


@pytest.mark.parametrize("pad", ["/instellingen/logo", "/instellingen/logo/verwijderen"])
def test_zonder_inlog_geen_wijziging(client, pad):
    r = client.post(pad, data={"logo": (io.BytesIO(png()), "l.png")})
    assert r.status_code == 302 and r.location.endswith("/inloggen")
    assert aantal_logos() == 0 and acties() == []


@pytest.mark.parametrize("pad", ["/instellingen/logo", "/instellingen/logo/verwijderen"])
def test_csrf_token_is_vereist(ingelogd, app, pad):  # noqa: F811
    vorig = logo_zetten()
    app.config["WTF_CSRF_ENABLED"] = True
    r = ingelogd.post(pad, data={"logo": (io.BytesIO(png(20, 20)), "l.png")})
    assert r.status_code == 400 and instellingen.logo() == vorig
    assert 'name="csrf_token"' in ingelogd.get("/instellingen").text.split("Logo opslaan")[0].split("<summary>Logo")[1]


def test_route_levert_alleen_een_logo_geen_foto_en_zonder_inlog(app):
    p = bezette_plaats(foto=png())
    foto = indeling.openbaar(p.publieke_sleutel)["foto"]
    client = app.test_client()
    assert client.get(f"/afbeelding/{foto}").status_code == 200
    assert client.get(f"/logo/{foto}").status_code == 404  # een foto komt niet via de logoroute
    assert client.get("/logo/0123456789abcdef").status_code == 404
    kenmerk = logo_zetten()
    assert client.get(f"/logo/{kenmerk}").status_code == 200  # openbaar, zoals de openbare pagina


def test_vereniging_en_logo_worden_geescaped_op_het_kaartje_en_de_openbare_pagina(app, ingelogd):  # noqa: F811
    x, geescapet = "<b>x</b>", "&lt;b&gt;x&lt;/b&gt;"
    p = bezette_plaats()
    instellingen.opslaan(x, CLI)
    logo_zetten()
    for tekst in (ingelogd.get(f"/kaartjes/print?plaats={p.id}").text,
                  app.test_client().get(f"/p/{p.publieke_sleutel}").text,
                  ingelogd.get("/instellingen").text):
        assert x not in tekst and geescapet in tekst


def test_tegelijk_uploaden_wacht_op_de_vergrendeling_en_vervangt_dan_het_nieuwe_logo(app):
    """Een beheerder wisselt het logo (vergrendelt de rij logo); een tweede upload wacht en vervangt
    daarna het logo van de eerste, niet het oude dat ze eerst las."""
    from tests.unit.hulp import race
    logo_zetten()
    oud = db.session.get(Instelling, "logo").waarde
    fouten = race(app, [
        "SELECT sleutel FROM instelling WHERE sleutel = 'logo' FOR UPDATE",
        ("INSERT INTO afbeelding (soort, mime_type, inhoud, breedte, hoogte, sleutel) "
         "VALUES ('logo', 'image/png', '\\x00', 1, 1, 'eerste')"),
        ("UPDATE instelling SET waarde = (SELECT id FROM afbeelding WHERE sleutel = 'eerste') "
         "WHERE sleutel = 'logo'"),
        f"DELETE FROM afbeelding WHERE id = {oud}"], {},
        lambda: instellingen.logo_vervangen(png(20, 20), CLI))
    assert fouten == [] and aantal_logos() == 1
    assert instellingen.logo() not in (None, "eerste")  # de tweede upload won, en de eerste is weg
    assert db.session.scalar(select(func.count()).select_from(Afbeelding)
                             .where(Afbeelding.sleutel == "eerste")) == 0


def test_plaats_zonder_logo_toont_op_het_kaartje_de_naam(ingelogd):  # noqa: F811
    p = plaats("A/1/1", ("Kajak",))
    tekst = ingelogd.get(f"/kaartjes/print?plaats={p.id}").text
    assert "kaartje-logo" not in tekst and "<p>Botenloods</p>" in tekst
