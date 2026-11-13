"""De webroutes en schermen van de bezetting als CSV (issue #158, ADR-014 §5): inlogplicht, recente
inlog, CSRF, de zes kolommen van het overzicht, geëscapete bestandsinhoud en de knoppen op /import-export."""

import io
import re
import time

import pytest
from sqlalchemy import select

from app.domein import Actor, bezetting_csv, csvbestand
from app.models import Beheerder, Bezettingsimport, Boot, Bootsoort, Naamkoppeling, db
from tests.unit.hulp import lid
from tests.unit.test_bezetting_csv import bestand, leg, plaats
from tests.unit.test_web_beheer import ingelogd  # noqa: F401  fixture


def uploaden(client, data, naam="bezetting.csv", **extra):
    return client.post("/bezetting/import", data={"bestand": (io.BytesIO(data), naam)},
                       content_type="multipart/form-data", **extra)


def uploader():
    return Actor.van(db.session.scalar(select(Beheerder)))


def pagina(client):
    return client.get("/bezetting/import").text


# Export


def test_web_export_en_sjabloon(ingelogd):  # noqa: F811
    leg("A/1/1", "Reiger", lid().id)
    r = ingelogd.get("/bezetting.csv")
    assert r.status_code == 200 and r.headers["Content-Type"] == "text/csv; charset=utf-8"
    assert r.headers["Content-Disposition"] == 'attachment; filename="bezetting.csv"'
    assert r.data == bezetting_csv.export() and b"A/1/1;Reiger;Kajak;Anna de Vries;1001" in r.data
    r = ingelogd.get("/bezetting.csv?leeg=1")
    assert r.headers["Content-Disposition"] == 'attachment; filename="bezetting-leeg.csv"'
    assert r.data == bezetting_csv.export(leeg=True) and b"# Voorbeeld" in r.data


def test_web_export_geeft_de_weigering_als_melding(ingelogd):  # noqa: F811
    from app.models import Plaats, Rek

    r = Rek(naam="#oud")
    db.session.add_all([r, Plaats(rek=r, verdieping=1, vak=1, publieke_sleutel="x" * 10,
                                  boot=Boot(naam="Reiger", bootsoort_id=1))])
    db.session.commit()
    r = ingelogd.get("/bezetting.csv", follow_redirects=True)
    assert "#oud begint met #" in r.text and r.request.path == "/import-export"


# Toegang

ROUTES = [("get", "/bezetting.csv"), ("post", "/bezetting/import"), ("get", "/bezetting/import"),
          ("post", "/bezetting/import/koppelen"), ("post", "/bezetting/import/bevestigen"),
          ("post", "/bezetting/import/annuleren"), ("get", "/bezetting/koppelingen"),
          ("post", "/bezetting/koppelingen/1/verwijderen")]


@pytest.mark.parametrize("methode, pad", ROUTES)
def test_web_vraagt_inloggen(client, methode, pad):
    r = getattr(client, methode)(pad)
    assert r.status_code == 302 and r.location.endswith("/inloggen")


@pytest.mark.parametrize("pad, data", [("/bezetting/import", True), ("/bezetting/import/bevestigen", False)])
def test_upload_en_bevestigen_vragen_een_recente_inlog(ingelogd, pad, data):  # noqa: F811
    plaats("A/1/1")
    bezetting_csv.uploaden(bestand("A/1/1;Reiger;Kajak;;"), uploader())
    with ingelogd.session_transaction() as s:
        s["ingelogd_op"] = int(time.time()) - 601
    if data:
        bezetting_csv.annuleren(uploader())
        r = uploaden(ingelogd, bestand("A/1/1;Reiger;Kajak;;"))
    else:
        r = ingelogd.post(pad)
    assert r.status_code == 302 and r.location.endswith("/inloggen")
    assert (db.session.scalar(select(Bezettingsimport)) is None) == data
    assert db.session.scalar(select(Boot).where(Boot.naam == "Reiger")) is None


def test_koppelen_annuleren_en_koppeling_verwijderen_vragen_alleen_een_inlog(ingelogd):  # noqa: F811
    bezetting_csv.uploaden(bestand("A/1/1;Reiger;Kajak;X;"), uploader())
    db.session.add(Naamkoppeling(naam="Annie", clubboot=True))
    db.session.commit()
    kid = db.session.scalar(select(Naamkoppeling.id))
    with ingelogd.session_transaction() as s:
        s["ingelogd_op"] = int(time.time()) - 601
    for pad in ("/bezetting/import/koppelen", f"/bezetting/koppelingen/{kid}/verwijderen",
                "/bezetting/import/annuleren"):
        r = ingelogd.post(pad, data={"keuze-2": "overslaan"})
        assert r.status_code == 302 and not r.location.endswith("/inloggen"), pad
    assert db.session.scalar(select(Bezettingsimport)) is None
    assert db.session.scalar(select(Naamkoppeling)) is None


@pytest.mark.parametrize("pad", [r[1] for r in ROUTES if r[0] == "post"])
def test_elke_post_vraagt_een_csrf_token(app, ingelogd, pad):  # noqa: F811
    app.config["WTF_CSRF_ENABLED"] = True  # zoals in productie
    r = ingelogd.post(pad, data={"bestand": (io.BytesIO(bestand("A/1/1;Reiger;Kajak;;")), "b.csv")},
                      content_type="multipart/form-data")
    assert r.status_code == 400 and db.session.scalar(select(Bezettingsimport)) is None


# Uploaden


def test_upload_toont_het_overzicht_met_de_zes_kolommen(ingelogd):  # noqa: F811
    plaats("A/1/1")
    r = uploaden(ingelogd, bestand("A/1/1;Reiger;Kajak;Anna de Vries;1001"), follow_redirects=True)
    assert r.request.path == "/bezetting/import"
    kop = re.findall(r'<th role="columnheader">([^<]+)</th>', r.text)
    assert kop == ["Regel", "Plaats", "Boot (bootsoort)", "Eigenaar (lidnummer)", "Uitkomst", "Keuze"]
    assert "Reiger (Kajak)" in r.text and '<span class="ds-tag">te koppelen</span>' in r.text
    assert "ds-notice--warning" in r.text and "ds-notice--danger" not in r.text  # nog te koppelen is geen systeemfout
    assert 'action="/bezetting/import/koppelen"' in r.text and 'name="csrf_token"' in r.text
    assert 'action="/bezetting/import/bevestigen"' in r.text and 'action="/bezetting/import/annuleren"' in r.text
    assert " style=" not in r.text and "<script" not in r.text


def test_het_overzicht_zonder_import_verwijst_terug_naar_import_export(ingelogd):  # noqa: F811
    r = ingelogd.get("/bezetting/import", follow_redirects=True)
    assert r.request.path == "/import-export" and "Er loopt geen bezettingsimport" in r.text


def test_een_tweede_upload_geeft_de_melding_en_laat_de_eerste_staan(ingelogd):  # noqa: F811
    uploaden(ingelogd, bestand("A/1/1;Reiger;Kajak;;"))
    r = uploaden(ingelogd, bestand("A/1/2;Fuut;Kajak;;"), follow_redirects=True)
    assert "Bevestig of annuleer die eerst" in r.text and r.request.path == "/import-export"
    assert "Bekijk het overzicht" in r.text
    assert [x["plaats"] for x in db.session.scalar(select(Bezettingsimport)).regels] == ["A/1/1"]


@pytest.mark.parametrize("data, naam, melding", [
    (None, "", "Kies een CSV-bestand."),
    (bestand("A/1/1;Reiger;Kajak;;"), "bezetting.xlsx", "extensie .csv"),
    (bestand("A/1/1;Reiger;Kajak;;"), "bezetting.txt", "extensie .csv"),
])
def test_upload_zonder_of_met_een_ander_bestandstype(ingelogd, data, naam, melding):  # noqa: F811
    r = ingelogd.post("/bezetting/import", data={"bestand": (io.BytesIO(data or b""), naam)},
                      content_type="multipart/form-data", follow_redirects=True)
    assert melding in r.text and db.session.scalar(select(Bezettingsimport)) is None


def test_upload_leest_niet_verder_dan_de_grens(ingelogd):  # noqa: F811
    r = uploaden(ingelogd, bestand("A/1/1;Reiger;Kajak;;") + b"#" + b"x" * csvbestand.MAX_BYTES)
    assert r.status_code == 422 and "groter dan 256 kB" in r.text
    assert db.session.scalar(select(Bezettingsimport)) is None


def test_upload_met_een_fout_in_de_opbouw_toont_de_regels_geescaped_en_bewaart_niets(ingelogd):  # noqa: F811
    r = uploaden(ingelogd, bestand("A/1/1;Reiger;Kajak;;", "<b>x</b>;1;2"))
    assert r.status_code == 422 and "<h1>Import/export</h1>" in r.text
    assert re.findall(r'aria-current="page">([^<]+)</a>', r.text) == ["Import/export"]
    assert "Het bestand is niet geïmporteerd. Er is niets veranderd." in r.text
    assert "<li>Regel 3: 5 kolommen verwacht, 3 gevonden.</li>" in r.text
    r = uploaden(ingelogd, bestand("A/1/1;Reiger;Kajak;;", kop="plaats;<b>x</b>;bootsoort;eigenaar;lidnummer"))
    assert "&lt;b&gt;x&lt;/b&gt;" in r.text and "<b>x</b>" not in r.text
    assert db.session.scalar(select(Bezettingsimport)) is None


# Bestandsinhoud op het scherm


VELDEN = ("plaats", "boot", "bootsoort", "eigenaar", "lidnummer")


def test_elk_veld_uit_het_bestand_staat_geescaped_op_het_overzicht(ingelogd):  # noqa: F811
    plaats("A/1/1")
    payload = {v: f"<b>{v}</b>" for v in VELDEN}
    uploaden(ingelogd, bestand(
        f"{payload['plaats']};Reiger;Kajak;;",
        f"A/1/1;{payload['boot']};{payload['bootsoort']};{payload['eigenaar']};{payload['lidnummer']}"))
    tekst = pagina(ingelogd)
    for veld, ruw in payload.items():
        assert ruw not in tekst, veld
        assert f"&lt;b&gt;{veld}&lt;/b&gt;" in tekst, veld
    assert "Plaats &lt;b&gt;plaats&lt;/b&gt; bestaat niet." in tekst  # de melding is ook geëscapet


def test_de_melding_van_een_fout_met_bestandsinhoud_is_geescaped(ingelogd):  # noqa: F811
    plaats("A/1/1")
    uploaden(ingelogd, bestand("A/1/1;Reiger;<b>x</b>;;"))
    tekst = pagina(ingelogd)
    assert "<b>x</b>" not in tekst and "De bootsoort &lt;b&gt;x&lt;/b&gt; bestaat niet" in tekst


def test_het_overzicht_toont_de_gevonden_eigenaar_en_zijn_keuzes(ingelogd):  # noqa: F811
    plaats("A/1/1")
    plaats("A/1/2")
    plaats("A/1/3")
    anna = lid("1001", "Anna de Vries")
    uploaden(ingelogd, bestand("A/1/1;Reiger;Kajak;Onbekend;", "A/1/2;Fuut;Zeilboot;;", "A/1/3;Meeuw;Kajak;Anna de Vries;1001"))
    tekst = pagina(ingelogd)
    # Regel 2 is te koppelen: de keuzelijst heeft de vereniging en de leden. Regel 3 heeft een onbekende soort
    # (de lijst heet soort-3, met overslaan en de soorten van de plaats), geen lid in de lijst.
    keuze2 = re.search(r'<select[^>]*id="keuze-2".*?</select>', tekst, re.DOTALL)[0]
    keuze3 = re.search(r'<select[^>]*id="soort-3".*?</select>', tekst, re.DOTALL)[0]
    assert 'value="club"' in keuze2 and f'value="{anna.id}"' in keuze2 and "Anna de Vries (1001)" in keuze2
    assert 'value="overslaan"' in keuze3 and ">Kajak</option>" in keuze3 and 'value="club"' not in keuze3
    assert "Anna" not in keuze3 and 'id="keuze-3"' not in tekst
    assert 'id="keuze-4"' not in tekst  # regel 4 is in orde: geen keuze nodig
    assert "<br>Gekoppeld: Anna de Vries (1001)" in tekst  # de gevonden eigenaar onder wat in het bestand stond
    assert "disabled" in tekst  # bevestigen kan nog niet


def test_koppelen_via_het_formulier_bewaart_de_keuze_en_ontgrendelt_bevestigen(ingelogd):  # noqa: F811
    plaats("A/1/1")
    anna = lid()
    uploaden(ingelogd, bestand("A/1/1;Reiger;Kajak;Onbekend;"))
    r = ingelogd.post("/bezetting/import/koppelen", data={"keuze-2": str(anna.id)}, follow_redirects=True)
    assert "De keuzes zijn opgeslagen." in r.text and r.request.path == "/bezetting/import"
    assert f'<option value="{anna.id}" selected>' in r.text and "disabled" not in r.text
    assert '<span class="ds-tag">nieuwe boot</span>' in r.text and "Alle regels zijn in orde" in r.text
    r = ingelogd.post("/bezetting/import/koppelen", data={"keuze-2": "424242"}, follow_redirects=True)
    assert "keuzes kloppen niet" in r.text


# Bevestigen en annuleren


def test_bevestigen_via_de_route_meldt_aantallen_en_zet_de_boot_op_de_plaats(ingelogd):  # noqa: F811
    p = plaats("A/1/1")
    lid()
    uploaden(ingelogd, bestand("A/1/1;Reiger;Kajak;;1001"))
    r = ingelogd.post("/bezetting/import/bevestigen", follow_redirects=True)
    assert r.request.path == "/import-export"
    assert ("De bezetting is geïmporteerd. Nieuwe boten: 1, toegewezen: 0, overschreven: 0, "
            "verplaatst: 0, ongewijzigd: 0, overgeslagen: 0.") in r.text
    assert "Bekijk het overzicht" not in r.text
    assert "Reiger" in ingelogd.get(f"/plaatsen/{p.id}").text
    assert "bezetting.geimporteerd" in ingelogd.get("/log/techniek").text
    assert "plaats.toegewezen" in ingelogd.get("/log").text


def test_bevestigen_met_een_open_regel_geeft_de_melding_zonder_bestandsinhoud_in_de_sessie(ingelogd):  # noqa: F811
    plaats("A/1/1")
    uploaden(ingelogd, bestand("A/1/1;Geheimeboot;Kajak;Geheimlid;"))
    r = ingelogd.post("/bezetting/import/bevestigen")
    with ingelogd.session_transaction() as s:
        assert "Geheim" not in str(dict(s)) and "regels te koppelen of met een fout" in str(dict(s))
    r = ingelogd.get(r.location)
    assert r.request.path == "/bezetting/import" and "Geheimeboot" in r.text
    assert db.session.scalar(select(Boot).where(Boot.naam == "Geheimeboot")) is None


def test_geen_flash_na_een_upload_of_koppeling_bevat_bestandsinhoud(ingelogd):  # noqa: F811
    plaats("A/1/1")
    lid()
    for stap in (lambda: uploaden(ingelogd, bestand("A/1/1;Geheimeboot;Kajak;Geheimlid;")),
                 lambda: uploaden(ingelogd, bestand("A/1/1;Geheimeboot;Kajak;Geheimlid;")),  # tweede upload
                 lambda: ingelogd.post("/bezetting/import/koppelen", data={"keuze-2": "overslaan"}),
                 lambda: ingelogd.post("/bezetting/import/annuleren")):
        stap()
        with ingelogd.session_transaction() as s:
            assert "Geheim" not in str(dict(s))


def test_annuleren_haalt_de_import_weg(ingelogd):  # noqa: F811
    uploaden(ingelogd, bestand("A/1/1;Reiger;Kajak;;"))
    r = ingelogd.post("/bezetting/import/annuleren", follow_redirects=True)
    assert "De import is geannuleerd." in r.text and db.session.scalar(select(Bezettingsimport)) is None
    r = ingelogd.post("/bezetting/import/annuleren", follow_redirects=True)
    assert "Er loopt geen bezettingsimport" in r.text


# Onthouden koppelingen


def test_koppelingen_scherm_toont_en_verwijdert_een_koppeling_en_escaped_de_naam(ingelogd):  # noqa: F811
    anna = lid()
    db.session.add_all([Naamkoppeling(naam="<b>naam</b>", lid_id=anna.id), Naamkoppeling(naam="De club", clubboot=True)])
    db.session.commit()
    tekst = ingelogd.get("/bezetting/koppelingen").text
    assert "<b>naam</b>" not in tekst and "&lt;b&gt;naam&lt;/b&gt;" in tekst
    assert "Anna de Vries" in tekst and "(clubboot)" in tekst and "Koppeling verwijderen" in tekst
    assert 'class="ds-btn ds-btn--danger">Koppeling verwijderen' in tekst
    kid = db.session.scalar(select(Naamkoppeling.id).where(Naamkoppeling.naam == "De club"))
    r = ingelogd.post(f"/bezetting/koppelingen/{kid}/verwijderen", follow_redirects=True)
    assert "De koppeling is verwijderd." in r.text and "De club" not in r.text
    r = ingelogd.post(f"/bezetting/koppelingen/{kid}/verwijderen", follow_redirects=True)
    assert "Deze koppeling bestaat niet." in r.text


def test_zonder_koppelingen_staat_er_een_melding(ingelogd):  # noqa: F811
    assert "Geen onthouden koppelingen" in ingelogd.get("/bezetting/koppelingen").text


# Knoppen op /import-export


def test_import_export_toont_de_knoppen_het_formulier_en_een_lopende_import(ingelogd):  # noqa: F811
    tekst = ingelogd.get("/import-export").text
    assert 'href="/bezetting.csv"' in tekst and 'href="/bezetting.csv?leeg=1"' in tekst
    assert 'href="/bezetting/koppelingen"' in tekst
    assert 'action="/bezetting/import"' in tekst and 'id="bezetting-bestand"' in tekst
    assert "Bekijk het overzicht" not in tekst and " style=" not in tekst and "<script" not in tekst
    uploaden(ingelogd, bestand("A/1/1;Reiger;Kajak;;"))
    tekst = ingelogd.get("/import-export").text
    assert 'href="/bezetting/import"' in tekst and "Er loopt een bezettingsimport" in tekst


def test_koppelingen_verwijst_naar_import_export(ingelogd):  # noqa: F811
    tekst = ingelogd.get("/bezetting/koppelingen").text
    assert re.search(r'<a class="ds-btn" href="/import-export">Naar Import/export</a>', tekst)


def test_de_route_voor_het_menu_item_en_de_bestaande_routes_zijn_er(app):
    regels = {r.rule: r.endpoint for r in app.url_map.iter_rules()}
    assert regels["/bezetting.csv"] == "web.bezetting_export"
    assert regels["/bezetting/import"] in ("web.bezetting_uploaden", "web.bezetting_import")
    assert regels["/bezetting/import/koppelen"] == "web.bezetting_koppelen"
    assert regels["/bezetting/koppelingen"] == "web.bezetting_koppelingen"


# Bootsoort kiezen (#202)


def cel(tekst, regel):
    """De cel Keuze van een regel."""
    return re.search(rf'<tr role="row">\s*<td role="cell" data-label="Regel">{regel}</td>.*?data-label="Keuze">(.*?)</td>',
                     tekst, re.DOTALL)[1]


def test_een_regel_met_twee_problemen_toont_twee_lijsten_in_een_fieldset(ingelogd):  # noqa: F811
    plaats("A/1/1", ("Kajak", "Surfski"))
    lid()
    uploaden(ingelogd, bestand("A/1/1;Reiger;Kayak;S. de Vrees;"))
    c = cel(pagina(ingelogd), 2)
    assert re.search(r'<fieldset[^>]*>\s*<legend class="dj-sr-only">Keuze voor regel 2</legend>', c)
    assert re.search(r'<label[^>]*for="soort-2">Bootsoort</label>', c)
    assert re.search(r'<label[^>]*for="keuze-2">Eigenaar</label>', c)
    soort_lijst = re.search(r'<select[^>]*id="soort-2".*?</select>', c, re.DOTALL)[0]
    eigenaar_lijst = re.search(r'<select[^>]*id="keuze-2".*?</select>', c, re.DOTALL)[0]
    assert 'value="overslaan"' in soort_lijst and ">Kajak</option>" in soort_lijst and ">Surfski</option>" in soort_lijst
    assert 'value="overslaan"' not in eigenaar_lijst and 'value="club"' in eigenaar_lijst
    assert "Kies bij een regel een bootsoort, een lid of de vereniging" in pagina(ingelogd)


def test_een_regel_met_een_probleem_houdt_een_lijst_met_het_label_keuze_voor_regel(ingelogd):  # noqa: F811
    plaats("A/1/1")
    plaats("A/1/2")
    lid()
    uploaden(ingelogd, bestand("A/1/1;Reiger;Kayak;;", "A/1/2;Fuut;Kajak;S. de Vrees;"))
    tekst = pagina(ingelogd)
    for regel, naam in ((2, "soort"), (3, "keuze")):
        c = cel(tekst, regel)
        assert "<fieldset" not in c and c.count("<select") == 1
        assert re.search(rf'<label class="dj-sr-only" for="{naam}-{regel}">Keuze voor regel {regel}</label>', c)


def test_een_fout_in_de_plaats_toont_alleen_regel_overslaan_in_soort_n(ingelogd):  # noqa: F811
    plaats("A/1/1")
    uploaden(ingelogd, bestand("Z/9/9;Reiger;Kajak;;"))
    c = cel(pagina(ingelogd), 2)
    assert 'name="soort-2"' in c and 'value="overslaan"' in c and c.count("<option") == 2
    assert 'name="keuze-2"' not in c


def test_na_het_opslaan_blijven_beide_lijsten_met_hun_keuze_staan(ingelogd):  # noqa: F811
    plaats("A/1/1", ("Kajak", "Surfski"))
    anna = lid()
    uploaden(ingelogd, bestand("A/1/1;Reiger;Kayak;S. de Vrees;"))
    r = ingelogd.post("/bezetting/import/koppelen", data={
        "soort-2": str(next(s.id for s in bezetting_csv.indeling.bootsoorten() if s.naam == "Surfski")),
        "keuze-2": str(anna.id)}, follow_redirects=True)
    c = cel(r.text, 2)
    assert "De keuzes zijn opgeslagen." in r.text and "<fieldset" in c
    assert ">Surfski</option>" in c and re.search(r'<option value="\d+" selected>Surfski</option>', c)
    assert f'<option value="{anna.id}" selected>' in c
    assert '<span class="ds-tag">nieuwe boot</span>' in r.text


def test_een_ongeldige_soort_via_het_formulier_geeft_een_melding_en_slaat_niets_op(ingelogd):  # noqa: F811
    plaats("A/1/1")
    uploaden(ingelogd, bestand("A/1/1;Reiger;Kayak;;"))
    r = ingelogd.post("/bezetting/import/koppelen", data={"soort-2": "424242"}, follow_redirects=True)
    assert "keuzes kloppen niet" in r.text
    assert db.session.scalar(select(Bezettingsimport)).keuzes == {}


def test_een_soortnaam_en_een_bootnaam_in_de_keuzecel_worden_geescaped(ingelogd):  # noqa: F811
    db.session.add(Bootsoort(naam="<b>x</b>"))
    db.session.commit()
    plaats("A/1/1", ("Kajak", "<b>x</b>"))
    uploaden(ingelogd, bestand("A/1/1;<i>y</i>;Kayak;;"))
    tekst = pagina(ingelogd)
    assert ">&lt;b&gt;x&lt;/b&gt;</option>" in tekst and "&lt;i&gt;y&lt;/i&gt;" in tekst
    assert "<b>x</b>" not in tekst and "<i>y</i>" not in tekst


def test_na_het_kiezen_van_alleen_een_soort_blijft_de_lijst_met_de_gekozen_soort_staan(ingelogd):  # noqa: F811
    plaats("A/1/1", ("Kajak", "Surfski"))
    uploaden(ingelogd, bestand("A/1/1;Reiger;Kayak;;"))
    surfski = next(s.id for s in bezetting_csv.indeling.bootsoorten() if s.naam == "Surfski")
    r = ingelogd.post("/bezetting/import/koppelen", data={"soort-2": str(surfski)}, follow_redirects=True)
    c = cel(r.text, 2)
    assert '<span class="ds-tag">nieuwe boot</span>' in r.text and "<fieldset" not in c
    assert f'<option value="{surfski}" selected>Surfski</option>' in c and 'name="keuze-2"' not in c
