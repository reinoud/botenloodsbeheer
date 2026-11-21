"""Het scherm Lid koppelen en de kolommen van Gebruikers (BV-96, issue #353 deel 2): elke actie, elke weigering,
het escapen van de lidnaam en de treffers voor een kijker. Het domein staat in test_lid_koppeling."""

import re
import time

import pytest
from sqlalchemy import select

from app.domein import beheerders, lidkeuze, vandaag
from app.models import Beheerder, db
from app.web import RECENT
from tests.unit.hulp import lid
from tests.unit.test_gebruikers_rollen import actor
from tests.unit.test_gebruikers_rollen import scherm as _scherm
from tests.unit.test_gebruikers_rollen import twee as _twee
from tests.unit.test_kijkers import als_kijker, main
from tests.unit.test_lid_koppeling import OUD, OUD_KIJKER, lid_van, logregels, oud_lid, zeg_op

twee = _twee  # fixtures
scherm = _scherm
XSS = "<b>x</b>"


def pad(b):
    return f"/gebruikers/{b.id}/lid"


def veldfout(tekst):
    m = re.search(r'<span class="ds-field__error" id="lid-zoek-fout">(.*?)</span>', tekst)
    return m and m[1]


# GET


def test_het_scherm_zonder_koppeling(scherm, twee):
    _, _, bert = twee
    r = scherm.get(pad(bert))
    assert r.status_code == 200
    t = main(r.text)
    assert "<h1>Lid koppelen: bert</h1>" in t and "Rol: Beheerder. Nu gekoppeld aan: niemand." in t
    assert 'name="actie" value="zoeken"' in t and "loskoppelen" not in t and 'value="koppelen"' not in t
    assert 'aria-current="true">Gebruikers' in r.text and "Terug naar Gebruikers" in t


def test_het_scherm_met_een_koppeling_toont_loskoppelen_en_de_tag_bij_een_oud_lid(scherm, twee):
    anna, _, bert = twee
    beheerders.lid_koppelen(bert.id, oud_lid().id, actor(anna))
    t = main(scherm.get(pad(bert)).text)
    assert "<h1>Lid wijzigen: bert</h1>" in t
    assert 'Nu gekoppeld aan: Oud (9) <span class="ds-tag">oud-lid</span>.' in t
    assert 'name="actie" value="loskoppelen" aria-label="Lid loskoppelen: bert"' in t
    assert "Zoek een ander lid: naam of lidnummer" in t


def test_onbekend_account_geeft_404(scherm):
    assert scherm.get("/gebruikers/9999/lid").status_code == 404
    assert scherm.post("/gebruikers/9999/lid", data={"actie": "loskoppelen"}).status_code == 404


# Zoeken


def test_zoeken_toont_de_treffers_en_koppelen_pas_dan(scherm, twee):
    _, _, bert = twee
    lid("1001", "Sanne de Vries")
    lid("1002", "Anna de Boer")
    t = main(scherm.post(pad(bert), data={"actie": "zoeken", "zoek": "de vries"}).text)
    assert 'name="lid_id" value="1001"' in t and "Anna de Boer" not in t
    assert "Treffers voor bert" in t and 'name="actie" value="koppelen"' in t
    assert lid_van(bert) is None


def test_zoeken_zonder_treffer_en_te_kort_geven_een_foutregel_bij_het_veld(scherm, twee):
    _, _, bert = twee
    assert veldfout(scherm.post(pad(bert), data={"actie": "zoeken", "zoek": "zzz"}).text) == lidkeuze.GEEN_LID
    assert veldfout(scherm.post(pad(bert), data={"actie": "zoeken", "zoek": "z"}).text) == lidkeuze.TE_KORT


def test_de_clubboot_is_geen_treffer(scherm, twee):
    """Mutant: club=True in _lid_veld. Dan geeft het zoeken op "clubboot" een rondje clubboot en geen foutregel."""
    r = scherm.post(pad(twee[2]), data={"actie": "zoeken", "zoek": "clubboot"})
    assert veldfout(r.text) == lidkeuze.GEEN_LID and 'name="lid_id" value="clubboot"' not in r.text


def test_een_kijker_krijgt_geen_oud_leden_als_treffer_een_beheerder_wel(scherm, twee):
    """Mutant: oud=True voor elke rol in _lid_veld. Dan staat het oud-lid ook voor de kijker in de treffers."""
    anna, _, bert = twee
    lid("1001", "Zand Actief")
    lid("1002", "Zand Oud", opzegdatum=vandaag())
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    kijker_t = main(scherm.post(pad(bert), data={"actie": "zoeken", "zoek": "zand"}).text)
    assert 'value="1001"' in kijker_t and 'value="1002"' not in kijker_t and "oud-lid</span>" not in kijker_t
    beheerder_t = main(scherm.post(pad(anna), data={"actie": "zoeken", "zoek": "zand"}).text)
    assert 'value="1001"' in beheerder_t and 'value="1002"' in beheerder_t and "oud-lid</span>" in beheerder_t


# Koppelen en loskoppelen


def test_koppelen_gaat_naar_gebruikers_met_een_melding_en_legt_het_vast(scherm, twee):
    _, _, bert = twee
    ld = lid("1002", "Anna de Boer")
    r = scherm.post(pad(bert), data={"actie": "koppelen", "lid_id": "1002", "zoek": "boer"})
    assert r.status_code == 302 and r.location == "/gebruikers"
    t = scherm.get("/gebruikers").text
    assert 'role="status">bert is gekoppeld aan Anna de Boer (1002).</div>' in t and "Lid: Anna de Boer (1002)" in t
    assert lid_van(bert) == ld.id and len(logregels("beheerder.lid_gewijzigd")) == 1


def test_loskoppelen_maakt_los_en_meldt_het(scherm, twee):
    anna, _, bert = twee
    beheerders.lid_koppelen(bert.id, lid().id, actor(anna))
    r = scherm.post(pad(bert), data={"actie": "loskoppelen"})
    assert r.status_code == 302 and r.location == "/gebruikers"
    t = scherm.get("/gebruikers").text
    assert "De koppeling van bert met een lid is losgemaakt." in t and "Lid: niet gekoppeld" in t
    assert lid_van(bert) is None


def test_koppelen_zonder_rondje_is_422_en_maakt_nooit_los(scherm, twee):
    """Een vergeten keuze is geen loskoppelen (review Aegis op BV-96). Mutant: koppelen zonder rondje valt
    door naar lid_id None."""
    anna, _, bert = twee
    ld = lid()
    beheerders.lid_koppelen(bert.id, ld.id, actor(anna))
    r = scherm.post(pad(bert), data={"actie": "koppelen", "zoek": "anna"})
    assert r.status_code == 422 and veldfout(r.text) == lidkeuze.NIET_GEKOZEN
    assert 'aria-invalid="true"' in r.text and 'aria-describedby="lid-zoek-hint lid-zoek-fout"' in r.text
    assert 'value="1001"' in r.text  # de treffers staan er weer, zonder eigen fout
    assert lid_van(bert) == ld.id and len(logregels("beheerder.lid_gewijzigd")) == 1


@pytest.mark.parametrize("zoek", ["", "x"], ids=["leeg", "te-kort"])
def test_koppelen_zonder_rondje_en_zonder_bruikbare_term_noemt_de_keuze_en_niet_de_zoekfout(scherm, twee, zoek):
    """Mutant: veld.fout or fout in _lid_veld. Dan wint de foutregel van het zoeken (te kort)."""
    r = scherm.post(pad(twee[2]), data={"actie": "koppelen", "zoek": zoek})
    assert r.status_code == 422 and veldfout(r.text) == lidkeuze.NIET_GEKOZEN


def test_een_onbekend_rondje_is_422(scherm, twee):
    _, _, bert = twee
    r = scherm.post(pad(bert), data={"actie": "koppelen", "lid_id": "9999", "zoek": "x"})
    assert r.status_code == 422 and veldfout(r.text) == lidkeuze.ONGELDIG and lid_van(bert) is None


@pytest.mark.parametrize("data", [{}, {"actie": ""}, {"actie": "opslaan"}, {"actie": "Koppelen", "lid_id": "1001"}],
                         ids=["zonder", "leeg", "onbekend", "hoofdletter"])
def test_een_onbekende_actie_is_400_en_wijzigt_niets(scherm, twee, data):
    anna, _, bert = twee
    ld = lid()
    beheerders.lid_koppelen(bert.id, ld.id, actor(anna))
    assert scherm.post(pad(bert), data=data).status_code == 400
    assert lid_van(bert) == ld.id and len(logregels("beheerder.lid_gewijzigd")) == 1


def test_een_kijker_aan_een_oud_lid_is_422_met_de_fout_bij_het_veld_ook_met_een_meegestuurde_waarde(scherm, twee):
    """De treffers tonen het oud-lid een kijker niet, maar de server weigert het ook bij een directe POST."""
    anna, _, bert = twee
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    oud_lid()
    r = scherm.post(pad(bert), data={"actie": "koppelen", "lid_id": "9", "zoek": "oud"})
    assert r.status_code == 422 and veldfout(r.text) == OUD and lid_van(bert) is None
    assert 'value="9"' not in r.text  # geen treffer voor een kijker


def test_een_beheerder_aan_een_oud_lid_mag(scherm, twee):
    _, _, bert = twee
    ld = oud_lid()
    r = scherm.post(pad(bert), data={"actie": "koppelen", "lid_id": "9", "zoek": "oud"})
    assert r.status_code == 302 and lid_van(bert) == ld.id


# Een kijker


def test_een_kijker_krijgt_403_op_het_scherm_en_op_elke_actie(app, twee):
    client, _ = als_kijker(app)
    _, _, bert = twee
    assert client.get(pad(bert)).status_code == 403
    for actie in ("zoeken", "koppelen", "loskoppelen"):
        assert client.post(pad(bert), data={"actie": actie, "lid_id": "1", "zoek": "ab"}).status_code == 403
    assert lid_van(bert) is None


def test_een_oude_inlog_moet_opnieuw_inloggen(scherm, twee):
    _, _, bert = twee
    with scherm.session_transaction() as s:
        s["ingelogd_op"] = time.time() - RECENT - 60  # nog binnen de sessie van 12 uur
    for r in (scherm.get(pad(bert)), scherm.post(pad(bert), data={"actie": "loskoppelen"})):
        assert r.status_code == 302 and r.location.startswith("/inloggen")


# Escapen (mutant: |safe op de naam)


def test_de_lidnaam_wordt_geescaped_op_gebruikers_en_op_lid_koppelen(scherm, twee):
    anna, _, bert = twee
    ld = lid("1001", XSS)
    beheerders.lid_koppelen(bert.id, ld.id, actor(anna))
    g = scherm.get("/gebruikers").text
    assert "Lid: &lt;b&gt;x&lt;/b&gt; (1001)" in g and XSS not in g
    # De stand op de pagina, de treffers en de zoekterm.
    r = scherm.post(pad(bert), data={"actie": "zoeken", "zoek": XSS + " 1001"})
    assert XSS not in r.text and "Nu gekoppeld aan: &lt;b&gt;x&lt;/b&gt; (1001)" in r.text
    r = scherm.post(pad(bert), data={"actie": "zoeken", "zoek": "1001"})
    assert "&lt;b&gt;x&lt;/b&gt; (1001)</label>" in r.text and XSS not in r.text
    r = scherm.post(pad(bert), data={"actie": "zoeken", "zoek": "x" + XSS})
    assert 'value="x&lt;b&gt;x&lt;/b&gt;"' in r.text and "x" + XSS not in r.text


def test_de_melding_na_het_koppelen_escapet_de_lidnaam(scherm, twee):
    _, _, bert = twee
    lid("1001", XSS)
    scherm.post(pad(bert), data={"actie": "koppelen", "lid_id": "1001", "zoek": "1001"})
    t = scherm.get("/gebruikers").text
    assert "bert is gekoppeld aan &lt;b&gt;x&lt;/b&gt; (1001)." in t and XSS not in t


# Gebruikers


def test_gebruikers_toont_per_account_het_lid_de_tag_en_de_link(scherm, twee):
    anna, _, bert = twee
    beheerders.lid_koppelen(anna.id, lid("1001", "Sanne").id, actor(anna))
    beheerders.lid_koppelen(bert.id, oud_lid().id, actor(anna))
    beheerders.uitnodigen("carla", "kijker", actor(anna))
    t = main(scherm.get("/gebruikers").text)
    carla = db.session.scalar(select(Beheerder).where(Beheerder.gebruikersnaam == "carla"))
    assert 'data-veld="lid">Lid: Sanne (1001)</p>' in t
    assert 'data-veld="lid">Lid: Oud (9) <span class="ds-tag">oud-lid</span></p>' in t
    assert 'data-veld="lid">Lid: niet gekoppeld</p>' in t
    assert t.count("Lid wijzigen<") == 2 and t.count("Lid koppelen<") == 1
    assert f'href="/gebruikers/{carla.id}/lid">Lid koppelen<span class="dj-sr-only">: carla</span>' in t
    assert t.count("ds-tag") == 1  # alleen het oud-lid


def test_gebruikers_heeft_beide_hints_en_uitnodigen_geen_lidveld(scherm):
    t = main(scherm.get("/gebruikers").text)
    assert 'Het lid koppel je daarna in de lijst met accounts.</p>' in t
    assert 'id="lid-hint">Wordt het lid van een kijker oud-lid, dan verwijdert de nachtelijke opschoning dat account; een beheerder blijft staan.</p>' in t
    uitnodigen = re.search(r'<form[^>]*action="/gebruikers".*?</form>', t, re.DOTALL)[0]
    assert 'name="lid' not in uitnodigen and 'type="search"' not in uitnodigen


def test_uitnodigen_via_het_scherm_negeert_een_meegestuurd_lid(scherm):
    lid("1001", "Sanne")
    scherm.post("/gebruikers", data={"gebruikersnaam": "carla", "rol": "kijker", "lid": "1001", "lid_id": "1001"})
    assert db.session.scalar(select(Beheerder.lid_id).where(Beheerder.gebruikersnaam == "carla")) is None


def test_maak_kijker_bij_een_oud_lid_is_een_alert_met_de_tekst_van_het_ontwerp(scherm, twee):
    anna, _, bert = twee
    ld = lid("5", "Straks oud")
    beheerders.lid_koppelen(bert.id, ld.id, actor(anna))
    zeg_op(ld, vandaag())
    r = scherm.post(f"/gebruikers/{bert.id}/rol", data={"rol": "kijker"}, follow_redirects=True)
    assert OUD_KIJKER in r.text and 'role="alert"' in r.text and "ds-notice--danger" in r.text
    assert r.request.path == "/gebruikers"
