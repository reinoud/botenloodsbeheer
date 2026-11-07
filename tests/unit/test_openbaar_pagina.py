"""Blok 2 van het nieuwe ontwerp (issue #150, BV-45): de openbare plaatspagina, antwoord eerst.
Elke toestand heeft een label en een zin; kop zonder link, skiplink en menu; invoer blijft geëscapet."""

import pytest

from app.domein import CLI, boten, toewijzing
from app.models import db
from tests.unit.hulp import beheerder_met_wachtwoord, lid, plaats, png
from tests.unit.test_web import inloggen

VRAAG = "Wil je een plaats in de loods?"


def pagina(client, p):
    return client.get(f"/p/{p.publieke_sleutel}").text


def bezet(code="A/1/1", boot="Zeemeeuw", eigenaar="Anna de Vries", club=False, foto=None):
    p = plaats(code, club=club)
    eigenaar_id = None if club else lid(naam=eigenaar).id
    toewijzing.toewijzen(p.id, boten.boot_aanmaken(boot, 1, eigenaar_id, foto, CLI).id, CLI)
    return p


def rekregel(p, tekst):
    p.rek.omschrijving = tekst
    db.session.commit()


def test_bezet_label_zin_en_foto(client):
    # Mutant: een andere zin, een boot of eigenaar buiten <strong>, of de foto weglaten valt hier.
    html = pagina(client, bezet(foto=png()))
    assert "<h1>Plaats A/1/1</h1>" in html
    assert '<span class="ds-tag">Bezet</span>' in html
    assert 'Hier hoort de <strong>Zeemeeuw</strong> van <strong>Anna de Vries</strong>.' in html
    assert 'class="bl-plaatsfoto"' in html and 'alt="Foto van Zeemeeuw"' in html
    assert "bl-plaats bl-plaats--foto" in html
    assert VRAAG not in html and "bl-tag--vrij" not in html


def test_bezet_zonder_foto_geen_img_en_geen_fotokolom(client):
    # Mutant: de img of de modifier ook zonder foto zetten valt hier.
    html = pagina(client, bezet())
    assert "<img" not in html.split("<main", 1)[1] and "bl-plaats--foto" not in html


def test_clubboot_is_clubplaats_met_de_vereniging_als_eigenaar(client):
    # Mutant: het label Bezet bij een clubboot, of de naam van het lid i.p.v. de vereniging, valt hier.
    html = pagina(client, bezet(club=True))
    assert '<span class="ds-tag">Clubplaats</span>' in html
    assert 'Hier hoort de <strong>Zeemeeuw</strong> van <strong>Botenloods</strong>.' in html
    assert VRAAG not in html


def test_vrije_plaats_label_zin_en_vraag(client):
    # Mutant: de vraag weglaten of het label zonder bl-tag--vrij valt hier.
    html = pagina(client, plaats())
    assert '<span class="ds-tag bl-tag--vrij">Vrij</span>' in html
    assert "Deze plaats is vrij." in html and "Hier hoort" not in html
    assert f'<p class="bl-vraag">{VRAAG} Vraag het de beheerder van de botenloods.</p>' in html
    assert "<img" not in html.split("<main", 1)[1]


def test_vrije_clubplaats_zegt_dat_ze_voor_een_clubboot_is(client):
    # Besluit stakeholder 2026-11-07. Mutant: de vlag clubplaats negeren geeft "Vrij" en de vraag.
    html = pagina(client, plaats(club=True))
    assert '<span class="ds-tag">Clubplaats</span>' in html
    assert "Deze plaats is voor een clubboot." in html
    assert VRAAG not in html and "Deze plaats is vrij." not in html and "bl-tag--vrij" not in html


def test_rekregel_zonder_label_en_alleen_met_omschrijving(client):
    # Mutant: een label "Rek" ervoor, of een lege regel zonder omschrijving, valt hier.
    p = plaats()
    assert "bl-rekregel" not in pagina(client, p)
    rekregel(p, "Stelling links")
    assert '<p class="bl-rekregel">Stelling links</p>' in pagina(client, p)


def test_kop_zonder_link_skiplink_menu_en_zoekveld(client):
    # Mutant: de skiplink, het menu of de link om het logo terugzetten valt hier.
    p = plaats()
    _b, geheim = beheerder_met_wachtwoord()
    anoniem = pagina(client, p)
    inloggen(client, geheim)
    ingelogd = pagina(client, p)
    for html in (anoniem, ingelogd):
        kop = html.split("<header", 1)[1].split("</header>", 1)[0]
        assert "<a " not in kop and '<span class="dj-logo">' in kop
        assert "dj-skip" not in html and "<details" not in html and "<nav" not in html
        assert "<input" not in html and "<form" not in html
        assert 'id="inhoud"' in html
    assert "dj-skip" in client.get("/").text and "<details" in client.get("/").text  # elders ongewijzigd


@pytest.mark.parametrize("veld", ["boot", "eigenaar", "omschrijving"])
def test_invoer_wordt_geescaped(client, veld):
    # Mutant: |safe op boot, eigenaar of omschrijving valt hier.
    p = bezet(boot="<b>x</b>" if veld == "boot" else "Zeemeeuw",
              eigenaar="<b>x</b>" if veld == "eigenaar" else "Anna de Vries")
    rekregel(p, "<b>x</b>" if veld == "omschrijving" else "Stelling")
    html = pagina(client, p)
    assert "<b>x</b>" not in html and "&lt;b&gt;x&lt;/b&gt;" in html


def test_onbekende_plaats_geeft_404_met_uitleg(client):
    r = client.get("/p/bestaatniet")
    assert r.status_code == 404
    assert "<h1>Deze pagina bestaat niet</h1>" in r.text
    assert "Controleer de link of scan de QR-code opnieuw." in r.text
    assert "dj-skip" not in r.text and '<span class="dj-logo">' in r.text
