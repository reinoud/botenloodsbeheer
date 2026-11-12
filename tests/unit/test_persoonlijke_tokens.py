"""Slice 10: persoonlijke tokens, robottokens uit de webinterface, rechten wijzigen, intrekken en
de tokenschermen (ADR-005 v1.4.0; BLB-030, BLB-031, BLB-032, BLB-035).

De domeinfuncties draaien als botenloods_web (de standaard van de fixture app); de aanroepen van
de API als de dienst api met de rol botenloods_api (fixture api)."""

import time

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.domein import CLI, SYSTEEM, Actor, Regelfout, beheerders, tokens
from app.models import Logregel, Token, db
from tests.unit.conftest import API, EIGENAAR
from tests.unit.hulp import beheerder_met_wachtwoord, race
from tests.unit.test_tokens import KOPPEL, app_uit_omgeving, bearer
from tests.unit.test_web import inloggen

BUITEN = {"X-Forwarded-For": "198.51.100.7"}  # een adres buiten KOPPELNET


@pytest.fixture
def twee():
    """(anna, geheim van anna, bert): twee actieve beheerders."""
    anna, geheim = beheerder_met_wachtwoord("anna")
    bert, _ = beheerder_met_wachtwoord("bert")
    return anna, geheim, bert


@pytest.fixture
def api(app, monkeypatch):
    return app_uit_omgeving(monkeypatch, DIENST="api").test_client()


@pytest.fixture
def scherm(client, twee):
    """Anna, ingelogd in de webinterface."""
    inloggen(client, twee[1])
    return client


def persoonlijk(b, naam="anna-laptop", rechten=("boten:lezen",), whitelist=(), dagen=None):
    return tokens.maken("persoonlijk", naam, list(rechten), list(whitelist), dagen, Actor.van(b))


def robot(b, naam="koppeling", rechten=("boten:lezen",), whitelist=("10.203.0.0/24",)):
    return tokens.maken("robot", naam, list(rechten), list(whitelist), None, Actor.van(b))


def logregels(actie):
    db.session.expire_all()
    return db.session.scalars(select(Logregel).where(Logregel.actie == actie)
                              .order_by(Logregel.id)).all()


def boten(api, waarde, headers=KOPPEL):
    return api.get("/api/v1/boten", headers=bearer(waarde) | headers)


# Maken (BLB-030, BLB-031)


def test_persoonlijk_token_hoort_bij_de_maker_met_logregel_zonder_waarde(app, twee):
    """BLB-030 criterium 1; ADR-005: token.gemaakt met soort persoonlijk en de eigenaar."""
    anna, _, _ = twee
    waarde = persoonlijk(anna)
    t = db.session.scalar(select(Token))
    assert (t.soort, t.beheerder_id, t.gemaakt_door, t.ip_whitelist) == (
        "persoonlijk", anna.id, "anna", [])
    [regel] = logregels("token.gemaakt")
    assert regel.actor_naam == "anna"
    assert regel.gegevens["soort"] == "persoonlijk" and regel.gegevens["eigenaar"] == "anna"
    assert waarde[12:] not in str([regel.gegevens, regel.verwijzingen])


def test_persoonlijk_token_hooguit_3_jaar(app, twee):
    """BLB-030 criterium 2: 1095 dagen mag, 1096 niet."""
    anna, _, _ = twee
    persoonlijk(anna, "drie-jaar", dagen=3 * 365)
    with pytest.raises(Regelfout, match="1095 dagen"):
        persoonlijk(anna, "te-lang", dagen=3 * 365 + 1)
    assert db.session.scalars(select(Token.naam)).all() == ["drie-jaar"]


def test_persoonlijk_token_zonder_leden_importeren(app, twee):
    """BLB-030 criterium 4: weigeren. Een robottoken krijgt het recht alleen met de CLI (#52)."""
    anna, _, _ = twee
    with pytest.raises(Regelfout, match="alleen bij een robottoken"):
        persoonlijk(anna, rechten=("boten:lezen", "leden:importeren"))
    with pytest.raises(Regelfout, match="alleen met de CLI"):
        robot(anna, rechten=("leden:importeren",))
    assert db.session.scalar(select(Token)) is None
    tokens.robot_maken("koppeling", ["leden:importeren"], [], None, CLI)
    assert db.session.scalar(select(Token.soort)) == "robot"


def test_alleen_de_cli_geeft_leden_importeren(app, twee):
    """#55, #118: een actor anders dan de CLI (token, taak, SYSTEEM) geeft of neemt het recht niet."""
    for actor in (Actor("token", 1, "robot.x"), Actor("taak", None, "ronde"), SYSTEEM):
        with pytest.raises(Regelfout, match="alleen met de CLI"):
            tokens.maken("robot", "via-token", ["leden:importeren"], ["10.0.0.0/8"], None, actor)
    tokens.robot_maken("met", ["leden:importeren"], [], None, CLI)
    met = db.session.scalar(select(Token))
    for actor in (Actor("token", 1, "robot.x"), SYSTEEM):
        tokens.rechten_wijzigen(met.id, ["boten:lezen"], actor)
        db.session.expire_all()
        assert db.session.get(Token, met.id).rechten == ["boten:lezen", "leden:importeren"]


def test_web_geeft_leden_importeren_niet_en_neemt_het_niet_af(app, twee):
    """#52: het web voegt het CLI-recht niet toe; een token met het recht uit de CLI houdt het.
    Ongewijzigd opslaan in een andere volgorde geeft geen logregel."""
    anna, _, _ = twee
    robot(anna, "zonder")
    tokens.robot_maken("met", ["leden:importeren", "bootaantallen:lezen"], [], None, CLI)
    zonder, met = db.session.scalars(select(Token).order_by(Token.naam.desc())).all()
    with pytest.raises(Regelfout, match="alleen met de CLI"):
        tokens.rechten_wijzigen(zonder.id, ["boten:lezen", "leden:importeren"], Actor.van(anna))
    tokens.rechten_wijzigen(met.id, ["bootaantallen:lezen"], Actor.van(anna))  # zoals het formulier
    assert not logregels("token.rechten_gewijzigd")
    tokens.rechten_wijzigen(met.id, ["leden:lezen"], Actor.van(anna))
    db.session.expire_all()
    assert db.session.get(Token, zonder.id).rechten == ["boten:lezen"]
    assert db.session.get(Token, met.id).rechten == ["leden:lezen", "leden:importeren"]
    tokens.rechten_wijzigen(met.id, ["boten:lezen"], CLI)  # de CLI kan het wel afnemen
    db.session.expire_all()
    assert db.session.get(Token, met.id).rechten == ["boten:lezen"]


def test_rechten_wijzigen_wacht_op_intrekken(app, twee):
    """FOR UPDATE in _actief: wie de rechten wijzigt terwijl een ander het token intrekt, wacht
    en krijgt daarna een fout; het ingetrokken token krijgt geen nieuwe rechten."""
    anna, _, _ = twee
    persoonlijk(anna)
    t = db.session.scalar(select(Token))
    fouten = race(app, ["SELECT id FROM token WHERE id = :t FOR UPDATE",
                        "UPDATE token SET ingetrokken_op = now() WHERE id = :t"],
                  {"t": t.id}, lambda: tokens.rechten_wijzigen(t.id, ["leden:lezen"],
                                                               Actor.van(anna)))
    assert fouten == ["Er is geen actief token met dit nummer."]
    assert db.session.get(Token, t.id).rechten == ["boten:lezen"]


def test_persoonlijk_token_alleen_door_een_beheerder(app):
    with pytest.raises(Regelfout, match="beheerder"):
        tokens.maken("persoonlijk", "cli-token", ["boten:lezen"], [], None, CLI)
    assert db.session.scalar(select(Token)) is None


def test_robot_uit_de_webinterface_heeft_een_whitelist_en_onthoudt_de_maker(app, twee):
    """BLB-031 criterium 4; ADR-005: whitelist verplicht bij robot, gemaakt_door als tekst."""
    anna, _, _ = twee
    with pytest.raises(Regelfout, match="whitelist nodig"):
        robot(anna, whitelist=())
    robot(anna)
    t = db.session.scalar(select(Token))
    assert (t.soort, t.beheerder_id, t.gemaakt_door) == ("robot", None, "anna")


def test_database_eist_beheerder_bij_persoonlijk_en_niet_bij_robot(app):
    """De check uit migratie 0009, als eigenaar (de rol van de migraties)."""
    engine = create_engine(EIGENAAR)
    for soort, beheerder in (("persoonlijk", "NULL"), ("robot", "1")):
        with engine.connect() as c, pytest.raises(IntegrityError, match="persoonlijk_met_beheerder"):
            c.execute(text(
                "INSERT INTO token (naam, soort, prefix, hash, rechten, ip_whitelist, verloopt_op,"
                f" beheerder_id, gemaakt_door) VALUES ('x', '{soort}', 'AAAAAAAA', 'x',"
                f" '{{boten:lezen}}', '{{10.0.0.0/8}}', now(), {beheerder}, 'cli')"))
    engine.dispose()


# Aanroepen met een persoonlijk token


def test_persoonlijk_token_met_lege_whitelist_werkt_vanaf_elk_adres(app, api, twee):
    """ADR-005: een lege whitelist betekent elk adres; de proxy begrenst (BLB-030 criterium 5,
    getoond met de proef op een losse Traefik)."""
    waarde = persoonlijk(twee[0])
    assert boten(api, waarde, BUITEN).status_code == 200
    assert boten(api, waarde, KOPPEL).status_code == 200


def test_persoonlijk_token_met_whitelist_weigert_daarbuiten(app, api, twee):
    waarde = persoonlijk(twee[0], whitelist=("203.0.113.0/24",))
    assert boten(api, waarde, {"X-Forwarded-For": "203.0.113.9"}).status_code == 200
    assert boten(api, waarde, BUITEN).status_code == 401


def test_geblokkeerde_eigenaar_weigert_tot_deblokkeren(app, api, twee):
    """BLB-030 criterium 3; ADR-005: blokkeren laat het token staan, reden eigenaar_inactief;
    na deblokkeren werkt het weer (besluit stakeholder 2026-11-03)."""
    anna, _, bert = twee
    waarde = persoonlijk(bert, "bert-laptop")
    assert boten(api, waarde).status_code == 200
    beheerders.blokkeren(bert.id, Actor.van(anna))
    r = boten(api, waarde)
    assert (r.status_code, r.json) == (401, {"fout": "Geen toegang."})
    [regel] = logregels("api.geweigerd")
    assert regel.gegevens["reden"] == "eigenaar_inactief" and regel.actor_naam == "bert-laptop"
    beheerders.deblokkeren(bert.id, Actor.van(anna))
    assert boten(api, waarde).status_code == 200


def test_verwijderen_neemt_persoonlijke_tokens_mee_als_web(app, api, twee):
    """BLB-030 criterium 3; ADR-005: de cascade draait met de rechten van de eigenaar van de
    tabel, dus deze test als botenloods_web (zonder DELETE op token) slaagt. Het log noemt het
    aantal tokens."""
    anna, _, bert = twee
    waarde = persoonlijk(bert, "bert-laptop")
    persoonlijk(bert, "bert-telefoon")
    persoonlijk(anna, "anna-laptop")
    assert db.session.execute(text("SELECT current_user")).scalar() == "botenloods_web"
    beheerders.verwijderen(bert.id, Actor.van(anna))
    assert db.session.scalars(select(Token.naam)).all() == ["anna-laptop"]
    [regel] = logregels("beheerder.verwijderd")
    assert regel.gegevens == {"gebruikersnaam": "bert", "tokens": 2}
    r = boten(api, waarde)
    assert r.status_code == 401
    assert logregels("api.geweigerd")[0].gegevens["reden"] == "onbekend"


def test_herstellen_laat_het_persoonlijke_token_werken(app, api, twee):
    """BLB-030 criterium 6 (besluit stakeholder 2026-11-03)."""
    anna, _, bert = twee
    waarde = persoonlijk(bert, "bert-laptop")
    beheerders.herstellen(bert.id, Actor.van(anna))
    assert boten(api, waarde).status_code == 200


def test_robot_blijft_werken_na_vertrek_van_de_maker(app, api, twee, scherm):
    """BLB-031 criteria 5 en 6: het token werkt en het overzicht noemt de maker nog."""
    anna, _, bert = twee
    waarde = robot(bert, "bert-koppeling")
    beheerders.verwijderen(bert.id, Actor.van(anna))
    assert boten(api, waarde).status_code == 200
    html = scherm.get("/tokens").get_data(as_text=True)
    assert '<td role="cell" data-label="Eigenaar of maker">bert</td>' in html


# Rechten wijzigen (BLB-032 criterium 4) en intrekken (BLB-035 criterium 2)


def test_rechten_gelden_vanaf_de_volgende_aanroep_met_logregel(app, api, twee):
    anna, _, bert = twee
    waarde = persoonlijk(anna, rechten=("boten:lezen",))
    assert api.get("/api/v1/leden", headers=bearer(waarde) | KOPPEL).status_code == 403
    t = db.session.scalar(select(Token))
    tokens.rechten_wijzigen(t.id, ["boten:lezen", "leden:lezen"], Actor.van(bert))
    assert api.get("/api/v1/leden", headers=bearer(waarde) | KOPPEL).status_code == 200
    [regel] = logregels("token.rechten_gewijzigd")
    assert regel.actor_naam == "bert" and regel.verwijzingen == [f"token:{t.id}"]
    assert regel.gegevens == {"naam": "anna-laptop", "oud": ["boten:lezen"],
                              "nieuw": ["boten:lezen", "leden:lezen"]}


@pytest.mark.parametrize("rechten,melding", [
    ([], "minstens één recht"), (["leden:schrijven"], "Onbekend recht"),
    (["boten:lezen", "persoonsgegevens"], "Onbekend recht: persoonsgegevens"),
    (["leden:importeren"], "alleen met de CLI")])
def test_ongeldige_rechten_wijzigen_niets(app, twee, rechten, melding):
    anna, _, _ = twee
    persoonlijk(anna)
    t = db.session.scalar(select(Token))
    with pytest.raises(Regelfout, match=melding):
        tokens.rechten_wijzigen(t.id, rechten, Actor.van(anna))
    db.session.expire_all()
    assert db.session.get(Token, t.id).rechten == ["boten:lezen"]
    assert not logregels("token.rechten_gewijzigd")


def test_ingetrokken_token_krijgt_geen_nieuwe_rechten(app, twee):
    anna, _, _ = twee
    persoonlijk(anna)
    t = db.session.scalar(select(Token))
    tokens.intrekken(t.id, Actor.van(anna))
    with pytest.raises(Regelfout, match="geen actief token"):
        tokens.rechten_wijzigen(t.id, ["leden:lezen"], Actor.van(anna))


def test_token_van_een_ander_intrekken(app, api, twee, scherm):
    """BLB-035 criterium 2, via de webinterface: anna trekt het token van bert in."""
    _anna, _, bert = twee
    waarde = persoonlijk(bert, "bert-laptop")
    t = db.session.scalar(select(Token))
    r = scherm.post(f"/tokens/{t.id}/intrekken", follow_redirects=True)
    assert "Het token is ingetrokken." in r.text and "Ingetrokken op " in r.text
    assert "Intrekken: bert-laptop" not in r.text and "<summary>bert-laptop</summary>" not in r.text
    [regel] = logregels("token.ingetrokken")
    assert regel.actor_naam == "anna" and regel.gegevens == {"naam": "bert-laptop"}
    assert boten(api, waarde).status_code == 401


# Tokenschermen


def test_overzicht_toont_alles_behalve_waarde_en_hash(app, twee, scherm):
    """BLB-035 criterium 1."""
    anna, _, _ = twee
    waarde = persoonlijk(anna, rechten=("boten:lezen", "leden:lezen"))
    t = db.session.scalar(select(Token))
    html = scherm.get("/tokens").get_data(as_text=True)
    for tekst in ('<td role="cell" data-label="Naam">anna-laptop</td>', '<td role="cell" data-label="Soort">persoonlijk</td>',
                  '<td role="cell" data-label="Eigenaar of maker">anna</td>',
                  '<td role="cell" data-label="Rechten">boten:lezen, leden:lezen</td>',
                  '<td role="cell" data-label="Whitelist">elk adres</td>',
                  '<td role="cell" data-label="Laatst gebruikt">nooit</td>', 'data-label="Verloopt op"'):
        assert tekst in html, tekst
    assert waarde[12:] not in html and t.hash not in html


def test_nieuw_token_toont_de_waarde_eenmalig_zonder_sessie(app, scherm):
    """BLB-030 criterium 1, BLB-031 criterium 4; ADR-005: geen redirect, no-store, geen flash."""
    r = scherm.post("/tokens/nieuw", data={
        "soort": "robot", "naam": "koppeling", "dagen": "30", "recht": ["boten:lezen", "leden:lezen"],
        "whitelist": "10.203.0.0/24, fd00::/64"})
    assert r.status_code == 200 and r.headers["Cache-Control"] == "no-store"
    [waarde] = [w for w in r.text.split() if tokens.TOKEN.search(w)]
    waarde = tokens.TOKEN.search(waarde)[0]
    with scherm.session_transaction() as s:
        assert "_flashes" not in s
    t = db.session.scalar(select(Token))
    assert (t.soort, t.rechten, [str(n) for n in t.ip_whitelist]) == (
        "robot", ["boten:lezen", "leden:lezen"], ["10.203.0.0/24", "fd00::/64"])
    assert waarde[12:] not in scherm.get("/tokens").text


@pytest.mark.parametrize("data,melding", [
    ({"dagen": "1096"}, "1095 dagen"), ({"dagen": "veel"}, "geef een aantal dagen"),
    ({"recht": ["leden:importeren"]}, "alleen bij een robottoken"),
    ({"whitelist": "10.0.0.1/8"}, "Whitelist"), ({"whitelist": "fe80::%eth0/64"}, "Whitelist"),
    ({"recht": []}, "minstens één recht")])
def test_nieuw_token_geweigerd_houdt_de_invoer(app, scherm, data, melding):
    invoer = {"soort": "persoonlijk", "naam": "anna-laptop", "dagen": "30",
              "recht": ["boten:lezen"], "whitelist": ""} | data
    r = scherm.post("/tokens/nieuw", data=invoer)
    assert r.status_code == 200 and melding in r.text and 'value="anna-laptop"' in r.text
    assert db.session.scalar(select(Token)) is None


@pytest.mark.parametrize("soort,whitelist,mag", [
    ("robot", "10.0.0.0/8, 2001:db8::/32", True), ("robot", "0.0.0.0/0", False),
    ("robot", "10.203.0.0/24, ::/0", False), ("persoonlijk", "0.0.0.0/0", True)])
def test_robottoken_in_het_scherm_weigert_een_te_brede_reeks(app, scherm, soort, whitelist, mag):
    # #243. Een persoonlijk token houdt een lege of brede whitelist (BLB-033, #255).
    r = scherm.post("/tokens/nieuw", data={"soort": soort, "naam": "koppeling", "dagen": "30",
                                           "recht": ["boten:lezen"], "whitelist": whitelist})
    assert r.status_code == 200 and ("niet breder zijn dan /8" in r.text) is not mag
    assert (db.session.scalar(select(Token)) is not None) is mag


def test_formulieren_tonen_leden_importeren_niet(app, scherm):
    """#52: niet te kiezen bij maken en wijzigen; bij een token dat het heeft een uitleg."""
    assert 'value="leden:importeren"' not in scherm.get("/tokens/nieuw").text
    tokens.robot_maken("koppeling", ["leden:importeren"], [], None, CLI)
    html = scherm.get("/tokens").text
    assert 'value="leden:importeren"' not in html and 'value="boten:lezen"' in html
    assert "alleen met de CLI te geven of af te nemen" in html


def test_formulier_vult_koppelnet_voor(app, scherm):
    html = scherm.get("/tokens/nieuw").text
    assert 'name="whitelist" type="text" value="10.203.0.0/24"' in html and 'value="365"' in html


@pytest.mark.parametrize("methode,pad", [
    ("get", "/tokens/nieuw"), ("post", "/tokens/nieuw"), ("post", "/tokens/{id}/rechten"),
    ("post", "/tokens/{id}/intrekken")])
def test_recente_inlog_vereist_voor_maken_wijzigen_en_intrekken(app, twee, scherm, methode, pad):
    """BLB-035 criterium 3 (ADR-001, ADR-005)."""
    persoonlijk(twee[0])
    t = db.session.scalar(select(Token))
    with scherm.session_transaction() as s:
        s["ingelogd_op"] = int(time.time()) - 601
    r = getattr(scherm, methode)(pad.format(id=t.id), data={
        "soort": "persoonlijk", "naam": "nieuw", "dagen": "30", "recht": ["leden:lezen"]})
    assert r.status_code == 302 and r.location.endswith("/inloggen")
    db.session.expire_all()
    t = db.session.get(Token, t.id)
    assert (t.rechten, t.ingetrokken_op) == (["boten:lezen"], None)
    assert db.session.scalar(select(db.func.count(Token.id))) == 1


def test_overzicht_kan_zonder_recente_inlog(app, scherm):
    with scherm.session_transaction() as s:
        s["ingelogd_op"] = int(time.time()) - 601
    assert scherm.get("/tokens").status_code == 200


def test_rechten_wijzigen_via_het_scherm(app, twee, scherm):
    persoonlijk(twee[0])
    t = db.session.scalar(select(Token))
    r = scherm.post(f"/tokens/{t.id}/rechten", data={"recht": ["leden:lezen"]},
                    follow_redirects=True)
    assert "De rechten zijn gewijzigd." in r.text
    db.session.expire_all()
    assert db.session.get(Token, t.id).rechten == ["leden:lezen"]


def test_menu_item_tokens(app, scherm):
    assert '<a class="dj-nav__link" href="/tokens">Tokens</a>' in scherm.get("/rekoverzicht").text


def test_bezoeker_gaat_naar_inloggen(client):
    for pad in ("/tokens", "/tokens/nieuw"):
        r = client.get(pad)
        assert r.status_code == 302 and r.location.endswith("/inloggen")
    assert client.post("/tokens/1/intrekken").status_code == 302


def test_api_rol_leest_van_beheerder_alleen_id_en_actief(app, twee):
    """Migratie 0009: botenloods_api leest of de eigenaar actief is, niet meer."""
    engine = create_engine(API)
    with engine.connect() as c:
        assert len(c.execute(text("SELECT id, actief FROM beheerder")).all()) == 2
        with pytest.raises(ProgrammingError, match="permission denied"):
            c.execute(text("SELECT gebruikersnaam FROM beheerder"))
    engine.dispose()
