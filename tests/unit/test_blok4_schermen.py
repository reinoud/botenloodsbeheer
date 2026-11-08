"""Blok 4 van het nieuwe ontwerp (issue #150, BV-64, designsystem 38d6463): toegang en beheer.
Geen startpagina (Eis 1), passkey eerst (1B, 2B), de antwoorden op de open vragen 1, 3, 4 en 6,
de bootsoorten die na een actie open staan (Eis 5), de zes webrechten (Eis 6), de rekken die op het
kaartjesscherm altijd open staan (5B) en de knoppen die als link kleur houden (#181)."""

import re
import time
from pathlib import Path

import pytest
from flask import render_template_string

from app.domein import CLI, beheerders, indeling, tokens
from app.models import Bootsoort, db
from tests.unit.hulp import WACHTWOORD, beheerder_met_wachtwoord, plaats
from tests.unit.test_beheerders_beheren import met_passkey
from tests.unit.test_web import inloggen

XSS = "<b>x</b>"
GEESCAPET = "&lt;b&gt;x&lt;/b&gt;"
STIJL = Path(__file__).parents[2] / "app" / "web" / "static" / "stijl.css"


@pytest.fixture
def ingelogd(client):
    b, geheim = beheerder_met_wachtwoord()
    inloggen(client, geheim)
    client.beheerder = b
    return client


def main(tekst):
    """Alleen de inhoud van de pagina: de kop heeft een eigen menu met een details."""
    return re.search(r"<main.*?</main>", tekst, re.DOTALL).group(0)


def wachtwoordblok(tekst):
    """De attributen van het blok met het wachtwoord op het inlogscherm: leeg (dicht) of " open"."""
    # data-wachtwoord is verplicht: passkey.js opent het blok zonder passkeys (BV-66).
    return re.search(r'<details class="dj-disclosure" data-wachtwoord([^>]*)>\s*<summary>Met wachtwoord en code',
                     tekst).group(1)


# Eis 1: geen startpagina


def test_wortel_stuurt_een_beheerder_naar_het_rekoverzicht_en_een_bezoeker_naar_inloggen(app, ingelogd):
    # Mutant: de route teruggeven aan een pagina (200) of de bezoeker doorsturen valt op de eerste of tweede assert.
    r = ingelogd.get("/")
    assert r.status_code == 302 and r.location == "/rekoverzicht"
    r = app.test_client().get("/")
    assert r.status_code == 302 and r.location.endswith("/inloggen")


def test_logo_in_de_kop_gaat_naar_het_rekoverzicht(ingelogd):
    # Mutant: base.html terug naar web.start laat het logo via een omweg lopen (href "/").
    assert 'class="dj-logo" href="/rekoverzicht"' in ingelogd.get("/rekoverzicht").text


def test_ingelogde_beheerder_op_inloggen_gaat_naar_het_rekoverzicht(ingelogd):
    # Mutant: inloggen.py:46 terug naar web.start geeft "/".
    assert ingelogd.get("/inloggen").location == "/rekoverzicht"


def test_geen_startpagina_meer(app):
    assert not (Path(app.root_path) / "web" / "templates" / "start.html").exists()
    assert "Welkom" not in main(app.test_client().get("/inloggen").text)


# 1B en open vraag 1: passkey eerst, wachtwoord in een uitklapblok


def test_inloggen_toont_de_passkey_eerst_en_het_wachtwoordblok_dicht(client):
    # Mutant: open als standaard valt op de tweede assert; de volgorde omkeren op de eerste.
    tekst = main(client.get("/inloggen").text)
    assert tekst.index('id="passkey-inloggen"') < tekst.index("Met wachtwoord en code")
    assert wachtwoordblok(tekst) == ""
    assert "Inloggen met passkey" in tekst and ">Verder<" in tekst


def test_wachtwoordblok_staat_open_na_een_mislukte_poging(client):
    # Mutant: open nooit zetten, of altijd, valt op deze of de vorige test.
    r = client.post("/inloggen", data={"gebruikersnaam": "bestaat-niet", "wachtwoord": "x" * 12},
                    follow_redirects=True)
    assert "Inloggen is mislukt." in r.text
    assert wachtwoordblok(main(r.text)) == " open"


def test_wachtwoordblok_blijft_dicht_bij_een_melding_die_geen_fout_is(client):
    # Mutant: de categorie weglaten uit get_flashed_messages laat elke melding het blok openen.
    with client.session_transaction() as s:
        s["_flashes"] = [("info", "Je bent uitgelogd.")]
    tekst = main(client.get("/inloggen").text)
    assert "Je bent uitgelogd." in tekst
    assert wachtwoordblok(tekst) == ""


def test_code_staat_in_een_paneel_met_een_formulier(client):
    beheerder_met_wachtwoord()
    client.post("/inloggen", data={"gebruikersnaam": "anna", "wachtwoord": WACHTWOORD})
    tekst = main(client.get("/inloggen/code").text)
    assert '<h1>Code uit je authenticator-app</h1>' in tekst
    assert re.search(r'<section class="dj-panel">\s*<form class="bl-formulier"', tekst)


# Open vraag 4: de verborgen h1 van het meldingsscherm


def test_meldingsscherm_heeft_een_verborgen_h1(client):
    # Mutant: de h1 of de klasse dj-sr-only weghalen.
    r = client.get("/uitnodiging/onzin")
    assert r.status_code == 404
    tekst = main(r.text)
    assert '<h1 class="dj-sr-only">Melding</h1>' in tekst
    assert "Naar inloggen" in tekst and 'role="alert"' in tekst


# 2B en open vragen 3 en 6


def test_uitnodiging_toont_de_passkey_eerst_en_het_wachtwoordblok_dicht(client):
    # Open vraag 3. Mutant: open op het blok, of de volgorde omkeren.
    code = beheerders.uitnodigen("carla", CLI)
    tekst = main(client.get(f"/uitnodiging/{code}").text)
    assert tekst.index('id="passkey-registreren"') < tekst.index("Wachtwoord en authenticator-app")
    # data-wachtwoord: passkey.js opent dit blok als de browser geen passkeys kent (BV-66).
    assert '<details class="dj-disclosure" data-wachtwoord>\n  <summary>Wachtwoord en authenticator-app</summary>' in tekst
    assert tekst.count('<h3 class="bl-subkop">') == 3  # wachtwoord, authenticator-app, code
    assert ">Wachtwoord instellen<" in tekst and 'class="bl-qr"' in tekst and 'id="totp-geheim"' in tekst


def test_profiel_zonder_passkey_heet_het_blok_passkey_toevoegen(ingelogd):
    # Open vraag 6. Mutant: de conditie omkeren valt hier en in de volgende test.
    tekst = main(ingelogd.get("/profiel").text)
    assert "<summary>Passkey toevoegen</summary>" in tekst and "Nog een passkey" not in tekst
    assert 'id="passkey-registreren"' in tekst


def test_profiel_met_een_passkey_heet_het_blok_nog_een_passkey(ingelogd):
    met_passkey(ingelogd.beheerder)
    tekst = main(ingelogd.get("/profiel").text)
    assert "<summary>Nog een passkey</summary>" in tekst and "<summary>Passkey toevoegen</summary>" not in tekst
    assert '<button type="button" class="ds-btn ds-btn--primary" id="passkey-registreren"' in tekst
    assert ">Passkey 1 intrekken<" in tekst and ">Wachtwoord intrekken<" in tekst


def test_profiel_met_wachtwoord_toont_geen_blok_om_het_toe_te_voegen(ingelogd):
    # Mutant: de conditie `not beheerder.wachtwoordhash` weghalen toont het blok ook hier.
    tekst = main(ingelogd.get("/profiel").text)
    assert "Wachtwoord en authenticator-app toevoegen" not in tekst and "totp-geheim" not in tekst


def test_profiel_zonder_wachtwoord_toont_het_blok_voor_toevoegen(client):
    b = beheerders.uitnodiging(beheerders.uitnodigen("dora", CLI)).beheerder
    met_passkey(b)
    with client.session_transaction() as s:
        s.update(beheerder_id=b.id, sessieversie=b.sessieversie, ingelogd_op=int(time.time()))
    tekst = main(client.get("/profiel").text)
    assert "<summary>Wachtwoord en authenticator-app toevoegen</summary>" in tekst
    assert ">Wachtwoord toevoegen<" in tekst and tekst.count('<h3 class="bl-subkop">') == 3
    assert "Wachtwoord intrekken" not in tekst


# Eis 5: Bootsoorten staat open na een actie


def test_bootsoorten_staat_dicht_zonder_actie_en_open_met_de_vraag(ingelogd):
    # Mutant: open altijd of nooit zetten, of een andere waarde van ?open= accepteren.
    assert '<details class="dj-disclosure" id="bootsoorten">' in ingelogd.get("/instellingen").text
    assert '<details class="dj-disclosure" id="bootsoorten">' in ingelogd.get("/instellingen?open=logo").text
    assert '<details class="dj-disclosure" id="bootsoorten" open>' in ingelogd.get("/instellingen?open=bootsoorten").text


def test_elke_actie_op_bootsoorten_laat_het_blok_open(ingelogd):
    # Mutant: _naar_bootsoorten() in een van de drie routes vervangen door de gewone redirect valt op de bijbehorende stap.
    r = ingelogd.post("/bootsoorten", data={"naam": "Waterfiets"})
    assert r.location == "/instellingen?open=bootsoorten#bootsoorten", "toevoegen"
    soort = next(s for s in indeling.bootsoorten() if s.naam == "Waterfiets")
    r = ingelogd.post(f"/bootsoorten/{soort.id}/naam", data={"naam": "Pedalo"})
    assert r.location == "/instellingen?open=bootsoorten#bootsoorten", "hernoemen"
    r = ingelogd.post(f"/bootsoorten/{soort.id}/verwijderen")
    assert r.location == "/instellingen?open=bootsoorten#bootsoorten", "verwijderen"


def test_geweigerde_actie_op_bootsoorten_toont_de_melding_in_een_open_blok(ingelogd):
    # Preview instellingen-bootsoorten: de melding en het open blok.
    p = plaats()
    soort = p.bootsoorten[0]
    r = ingelogd.post(f"/bootsoorten/{soort.id}/verwijderen", follow_redirects=True)
    assert 'role="alert"' in r.text and "is in gebruik bij 1 plaats" in r.text
    assert 'id="bootsoorten" open>' in r.text


def test_instellingen_toont_logo_en_bootsoorten_als_blokken_en_de_naam_in_een_paneel(ingelogd):
    tekst = main(ingelogd.get("/instellingen").text)
    assert re.search(r'<details class="dj-disclosure">\s*<summary>Logo</summary>', tekst)
    assert "Er is geen logo" in tekst and "huisstijl</code>" not in tekst
    assert '<section class="dj-panel" aria-labelledby="naam-kop">' in tekst
    assert tekst.count('data-label="Bootsoort"') == len(indeling.bootsoorten()) and "<table" not in tekst
    assert 'name="soort-nieuw"' not in tekst and 'id="soort-nieuw" name="naam"' in tekst


def test_instellingen_escapet_de_naam_van_een_bootsoort(ingelogd):
    # Mutant: |safe op s.naam valt hier. De rij gaat rechtstreeks de database in: het domein weigert een / in de naam.
    db.session.add(Bootsoort(naam=XSS))
    db.session.commit()
    tekst = ingelogd.get("/instellingen?open=bootsoorten").text
    assert XSS not in tekst and GEESCAPET in tekst
    assert f"Nieuwe naam voor {GEESCAPET}" in tekst and f"{GEESCAPET} verwijderen" in tekst


# Eis 6: de zes webrechten


def test_token_maken_toont_de_zes_webrechten_en_niet_leden_importeren(ingelogd):
    # Mutant: de rechten uit RECHTEN in plaats van WEBRECHTEN laat leden:importeren verschijnen.
    tekst = main(ingelogd.get("/tokens/nieuw").text)
    assert re.findall(r'name="recht" value="([^"]+)"', tekst) == list(tokens.WEBRECHTEN) and len(tokens.WEBRECHTEN) == 6
    assert "leden:importeren" not in tekst
    assert "Wie en hoe lang" in tekst and "Wat mag het token" in tekst
    assert tekst.count('class="bl-radio"') == 2 and tekst.count("bl-vast") == 1


def test_token_met_leden_importeren_toont_de_cli_zin(ingelogd):
    # Mutant: de conditie of de zin weghalen.
    tokens.robot_maken("met-import", ["leden:importeren", "boten:lezen"], [], None, CLI)
    tokens.robot_maken("zonder-import", ["boten:lezen"], [], None, CLI)
    tekst = main(ingelogd.get("/tokens").text)
    assert tekst.count("alleen met de CLI te geven of af te nemen") == 1
    assert "leden:importeren" in tekst and tekst.count('value="leden:importeren"') == 0
    assert len(re.findall(r'<details class="dj-disclosure">', tekst)) == 2


# 4B: eenmalige waarde in een kader, zonder kopieerknop


def test_tokenwaarde_staat_in_een_kader_met_waarschuwing_en_zonder_kopieerknop(ingelogd):
    r = ingelogd.post("/tokens/nieuw", data={"soort": "persoonlijk", "naam": "laptop", "dagen": "30",
                                             "recht": ["boten:lezen"]})
    tekst = main(r.text)
    assert re.search(r'<div class="bl-waarde"><code id="tokenwaarde">[^<]+</code></div>', tekst)
    assert "ds-notice--warning" in tekst and "Kopieer de waarde nu." in tekst
    assert '<a class="ds-btn" href="/tokens">Terug naar tokens</a>' in tekst
    assert "<button" not in tekst  # geen kopieerknop (BV-64, 4B)


def test_uitnodigingslink_staat_in_een_kader_met_waarschuwing_en_zonder_kopieerknop(ingelogd):
    r = ingelogd.post("/beheerders", data={"gebruikersnaam": "carla"})
    tekst = main(r.text)
    assert re.search(r'<div class="bl-waarde"><code id="uitnodigingslink">[^<]+/uitnodiging/[^<]+</code></div>', tekst)
    assert "ds-notice--warning" in tekst and "Hij werkt één keer" in tekst
    assert '<a class="ds-btn" href="/beheerders">Terug naar beheerders</a>' in tekst
    assert "<button" not in tekst


# 5B: de rekken staan altijd open


def test_kaartjesscherm_toont_elk_rek_als_vak_zonder_uitklapblok(ingelogd):
    # Mutant: een details om het vak, of "Heel rek" niet eerst, of een rek zonder plaatsen tonen.
    plaats(code="R/1/1")
    tekst = main(ingelogd.get("/kaartjes").text)
    assert "<details" not in tekst
    assert re.search(r'<fieldset class="dj-choices dj-choices--columns bl-rekkeuze">\s*<legend>R</legend>\s*'
                     r'<div class="ds-check bl-rekheel"><input type="checkbox" id="rek-\d+" name="rek"', tekst)
    assert re.search(r'<legend>R</legend>.*?>Heel R<.*?>R/1/1<', tekst, re.DOTALL)
    assert re.search(r'<div class="bl-vast"><button type="submit" class="ds-btn ds-btn--primary">Kaartjes maken</button>', tekst)


def test_kaartjesscherm_zonder_plaatsen_zegt_dat_er_geen_zijn(ingelogd):
    # Mutant: de else-tak weghalen.
    tekst = main(ingelogd.get("/kaartjes").text)
    assert "Er zijn nog geen plaatsen." in tekst and "<fieldset" not in tekst and "Kaartjes maken" in tekst


# Knoppen en tabellen (3A, 6A, 7A)


@pytest.mark.parametrize("pad", ["/beheerders", "/tokens", "/status"])
def test_tabellen_staan_in_bl_tabel(ingelogd, pad):
    # Mutant: de wrapperklasse terug naar tabel.
    tokens.robot_maken("koppeling", ["boten:lezen"], ["192.0.2.1"], None, CLI)
    tekst = main(ingelogd.get(pad).text)
    assert '<div class="ds-table-wrap bl-tabel">' in tekst and 'class="ds-table-wrap tabel"' not in tekst


# Escapen van invoer in de nieuwe macro en de nieuwe knoppen


def test_wachtwoordformulier_escapet_elk_argument(app):
    # Mutant: |safe op {{ actie }}, {{ knop }}, {{ qr }} of {{ geheim }} in _wachtwoord.html: een per tak.
    with app.test_request_context():
        html = render_template_string(
            '{% from "_wachtwoord.html" import wachtwoordformulier %}'
            "{{ wachtwoordformulier(a, k, q, g) }}", a=XSS, k=XSS + "k", q=XSS + "q", g=XSS + "g")
    assert XSS not in html
    for deel in (f'action="{GEESCAPET}"', f"{GEESCAPET}k</button>", f'src="{GEESCAPET}q"', f"{GEESCAPET}g</code>"):
        assert deel in html, deel


def test_profiel_escapet_de_naam_van_een_passkey(ingelogd):
    # Mutant: |safe op p.naam in de titel, in de knoptekst of in de macro intrekken.
    met_passkey(ingelogd.beheerder, naam=XSS)
    tekst = ingelogd.get("/profiel").text
    assert XSS not in tekst
    assert f'data-label="Inlogmethode">{GEESCAPET}</span>' in tekst and f"{GEESCAPET} intrekken</button>" in tekst


def test_link_en_tokenwaarde_escapen_hun_invoer(app):
    # Mutant: |safe op titel, uitleg of link in link.html, of op naam of waarde in token_waarde.html.
    with app.test_request_context():
        link = render_template_string(
            '{% extends "link.html" %}', titel=XSS + "t", uitleg=XSS + "u", link=XSS + "l")
        waarde = render_template_string(
            '{% extends "token_waarde.html" %}', naam=XSS + "n", waarde=XSS + "w")
    assert XSS not in link and XSS not in waarde
    for deel in (f"{GEESCAPET}t", f"{GEESCAPET}u", f"{GEESCAPET}l</code>"):
        assert deel in link, deel
    for deel in (f"Token {GEESCAPET}n gemaakt", f"{GEESCAPET}w</code>"):
        assert deel in waarde, deel


# #181: een knop die een link is, houdt de kleur van de knop


def test_link_in_main_slaat_knoppen_over():
    # Mutant: de selector terug naar `.bl-main :where(a)` laat a.ds-btn--primary blauw op blauw (#181).
    css = STIJL.read_text()
    assert ".bl-main :where(a:not(.ds-btn)) { color: var(--brand-mid);" in css
    assert ".bl-main :where(a) {" not in css
    assert not re.search(r"\.bl-main a\.ds-btn[^{]*\{[^}]*color", css)  # geen lokale correctie meer nodig


def test_gewone_link_houdt_brand_mid(ingelogd):
    # Gewone links in main hebben geen ds-btn; tokens.html heeft een knoplink en een gewone link.
    tekst = main(ingelogd.get("/tokens").text)
    assert '<a class="ds-btn ds-btn--primary" href="/tokens/nieuw">Token maken</a>' in tekst
