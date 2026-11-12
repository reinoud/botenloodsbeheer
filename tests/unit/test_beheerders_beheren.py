"""Beheerders beheren (BLB-023) en de eigen inlogmethodes toevoegen of intrekken (BLB-038),
volgens ADR-001 v1.1.0: recente inlog van 10 minuten, intrekken beëindigt alle eigen sessies."""

import re
import time

import pytest
import segno
from cryptography.fernet import Fernet
from sqlalchemy import select

from app.domein import CLI, Actor, Regelfout, beheerders
from app.models import Beheerder, Logregel, Passkey, Uitnodiging, db
from tests.unit.hulp import WACHTWOORD, beheerder_met_wachtwoord, code_bij, race
from tests.unit.test_web import inloggen


def actor(b):
    return Actor.van(b)


def met_passkey(b, naam="Passkey 1"):
    """Een passkey zoals na registratie; de WebAuthn-controle zelf toetst de E2E-test."""
    db.session.add(Passkey(beheerder_id=b.id, credential_id=naam.encode(), publieke_sleutel=b"x",
                           teller=0, naam=naam))
    db.session.commit()
    return db.session.scalar(select(Passkey).where(Passkey.naam == naam))


def logacties():
    return [r.actie for r in db.session.scalars(select(Logregel).order_by(Logregel.id))]


@pytest.fixture
def twee():
    """(anna, geheim van anna, bert): twee actieve beheerders met wachtwoord en TOTP."""
    anna, geheim = beheerder_met_wachtwoord("anna")
    bert, _ = beheerder_met_wachtwoord("bert")
    return anna, geheim, bert


# BLB-023


def test_uitgenodigde_beheerder_kan_inloggen_met_dezelfde_rechten(app, twee):
    anna, _, _ = twee
    code = beheerders.uitnodigen("carla", actor(anna))
    geheim = beheerders.nieuw_totp_geheim()
    carla = beheerders.wachtwoord_instellen(code, WACHTWOORD, geheim, code_bij(geheim))
    assert beheerders.wachtwoord_controleren("carla", WACHTWOORD) == carla
    beheerders.blokkeren(anna.id, actor(carla))  # dezelfde rechten


def test_blokkeren_beeindigt_sessie_en_inloggen(app, twee):
    anna, _, bert = twee
    versie = bert.sessieversie
    beheerders.blokkeren(bert.id, actor(anna))
    bert = db.session.get(Beheerder, bert.id)
    assert not bert.actief and bert.sessieversie == versie + 1
    assert beheerders.wachtwoord_controleren("bert", WACHTWOORD) is None
    assert "beheerder.geblokkeerd" in logacties()
    beheerders.deblokkeren(bert.id, actor(anna))
    assert beheerders.wachtwoord_controleren("bert", WACHTWOORD) == bert


@pytest.mark.parametrize("functie", ["blokkeren", "verwijderen", "herstellen"])
def test_eigen_account_en_laatste_actieve_account_geweigerd(app, twee, functie):
    anna, _, bert = twee
    beheerders.blokkeren(bert.id, actor(anna))
    # anna is nu het laatste actieve account.
    with pytest.raises(Regelfout, match="altijd een actieve beheerder"):
        getattr(beheerders, functie)(anna.id, actor(anna))
    assert db.session.get(Beheerder, anna.id).actief


def test_geblokkeerde_actor_kan_niets(app, twee):
    anna, _, bert = twee
    beheerders.blokkeren(bert.id, actor(anna))
    with pytest.raises(Regelfout, match="niet meer actief"):
        beheerders.blokkeren(anna.id, actor(bert))


def test_verwijderen_met_passkeys_en_log(app, twee):
    anna, _, bert = twee
    met_passkey(bert)
    beheerders.verwijderen(bert.id, actor(anna))
    assert db.session.get(Beheerder, bert.id) is None
    assert db.session.scalar(select(Passkey)) is None
    r = db.session.scalars(select(Logregel).order_by(Logregel.id.desc())).first()
    assert r.actie == "beheerder.verwijderd" and r.gegevens == {"gebruikersnaam": "bert", "tokens": 0}


def test_herstel_trekt_alles_in_en_geeft_nieuwe_link(app, twee):
    anna, _, bert = twee
    met_passkey(bert)
    versie = bert.sessieversie
    code = beheerders.herstellen(bert.id, actor(anna))
    bert = db.session.get(Beheerder, bert.id)
    assert bert.wachtwoordhash is None and bert.totp_geheim is None and not bert.passkeys
    assert bert.sessieversie == versie + 1
    assert beheerders.wachtwoord_controleren("bert", WACHTWOORD) is None
    # Alleen de nieuwe uitnodiging bestaat nog; de helper ziet geen wachtwoord of geheim.
    assert len(db.session.scalars(select(Uitnodiging)
                                  .where(Uitnodiging.beheerder_id == bert.id)).all()) == 1
    geheim = beheerders.nieuw_totp_geheim()
    beheerders.wachtwoord_instellen(code, "nieuw wachtwoord 123", geheim, code_bij(geheim))
    regel = db.session.scalar(select(Logregel).where(Logregel.actie == "beheerder.hersteld"))
    assert code not in str(regel.gegevens)


def test_herstel_van_geblokkeerd_account_geweigerd(app, twee):
    anna, _, bert = twee
    beheerders.blokkeren(bert.id, actor(anna))
    with pytest.raises(Regelfout, match="Deblokkeer het eerst"):
        beheerders.herstellen(bert.id, actor(anna))


def test_gelijktijdig_elkaar_blokkeren(app, twee):
    """Anna blokkeert bert terwijl bert anna blokkeert. Zonder FOR UPDATE op de actieve accounts
    zouden beide slagen en is er geen actieve beheerder meer."""
    anna, _, bert = twee
    fouten = race(app, ["SELECT id FROM beheerder WHERE id = :b FOR UPDATE",
                        "UPDATE beheerder SET actief = false WHERE id = :b"],
                  {"b": bert.id}, lambda: beheerders.blokkeren(anna.id, actor(bert)))
    assert fouten == ["Je account is niet meer actief."]
    assert db.session.get(Beheerder, anna.id).actief


# BLB-038


def test_wachtwoord_toevoegen_werkt_pas_na_juiste_code(app):
    code = beheerders.uitnodigen("anna", CLI)
    anna = beheerders.uitnodiging(code).beheerder
    met_passkey(anna)
    geheim = beheerders.nieuw_totp_geheim()
    with pytest.raises(Regelfout, match="klopt niet"):
        beheerders.wachtwoord_toevoegen(WACHTWOORD, geheim, "abcdef", actor(anna))
    assert db.session.get(Beheerder, anna.id).wachtwoordhash is None
    beheerders.wachtwoord_toevoegen(WACHTWOORD, geheim, code_bij(geheim), actor(anna))
    assert beheerders.wachtwoord_controleren("anna", WACHTWOORD) == anna
    r = db.session.scalars(select(Logregel).where(Logregel.actie == "beheerder.methode_toegevoegd")
                           .order_by(Logregel.id.desc())).first()
    assert r.gegevens == {"methode": "wachtwoord en TOTP"}  # geen wachtwoord of geheim
    with pytest.raises(Regelfout, match="al een wachtwoord"):
        beheerders.wachtwoord_toevoegen(WACHTWOORD, geheim, code_bij(geheim, 1), actor(anna))


def test_ongeldige_passkey_toevoegen_geweigerd(app):
    anna, _ = beheerder_met_wachtwoord()
    with pytest.raises(Regelfout, match="kon niet worden geregistreerd"):
        beheerders.passkey_toevoegen({"id": "x", "rawId": "x"}, b"challenge", actor(anna))
    assert not db.session.get(Beheerder, anna.id).passkeys


def test_intrekken_van_een_van_twee_methodes(app):
    anna, _ = beheerder_met_wachtwoord()
    met_passkey(anna)
    versie = anna.sessieversie
    beheerders.methode_intrekken(None, actor(anna))
    anna = db.session.get(Beheerder, anna.id)
    assert anna.wachtwoordhash is None and anna.totp_geheim is None and len(anna.passkeys) == 1
    assert anna.sessieversie == versie + 1
    assert beheerders.wachtwoord_controleren("anna", WACHTWOORD) is None
    regel = db.session.scalars(select(Logregel).order_by(Logregel.id.desc())).first()
    assert regel.actie == "beheerder.methode_ingetrokken"
    assert regel.gegevens == {"methode": "wachtwoord en TOTP"}


@pytest.mark.parametrize("methode", ["wachtwoord", "passkey"])
def test_enige_methode_intrekken_geweigerd(app, methode):
    if methode == "wachtwoord":
        anna, _ = beheerder_met_wachtwoord()
        passkey_id = None
    else:
        anna = beheerders.uitnodiging(beheerders.uitnodigen("anna", CLI)).beheerder
        passkey_id = met_passkey(anna).id
    with pytest.raises(Regelfout, match="enige inlogmethode"):
        beheerders.methode_intrekken(passkey_id, actor(anna))


def test_passkey_van_een_ander_intrekken_geweigerd(app, twee):
    anna, _, bert = twee
    met_passkey(anna)
    van_bert = met_passkey(bert, "Passkey van bert")
    with pytest.raises(Regelfout, match="bestaat niet"):
        beheerders.methode_intrekken(van_bert.id, actor(anna))


def test_gelijktijdig_beide_methodes_intrekken(app):
    """Twee tabbladen trekken tegelijk elk een andere methode in. Het account wordt vergrendeld,
    dus de tweede ziet dat er nog maar één methode is."""
    anna, _ = beheerder_met_wachtwoord()
    passkey = met_passkey(anna)
    fouten = race(app, ["SELECT id FROM beheerder WHERE id = :a FOR UPDATE",
                        "DELETE FROM passkey WHERE id = :p"],
                  {"a": anna.id, "p": passkey.id},
                  lambda: beheerders.methode_intrekken(None, actor(anna)))
    assert fouten == ["Dit is je enige inlogmethode. Voeg eerst een andere toe."]
    assert db.session.get(Beheerder, anna.id).wachtwoordhash is not None


def _geladen_en_intrekken(beheerder_id, passkey_id):
    """Zoals de webroute: laad_beheerder heeft het account en de passkeys al geladen."""
    b = db.session.get(Beheerder, beheerder_id)
    len(b.passkeys)
    beheerders.methode_intrekken(passkey_id, Actor.van(b))


def test_gelijktijdig_intrekken_met_vooraf_geladen_account(app):
    """Het ene tabblad trekt het wachtwoord in, het andere de enige passkey. Het tweede had het
    account al geladen en moet na de vergrendeling de nieuwe stand zien (review aegis)."""
    anna, _ = beheerder_met_wachtwoord()
    passkey = met_passkey(anna)
    fouten = race(app, ["SELECT id FROM beheerder WHERE id = :a FOR UPDATE",
                        ("UPDATE beheerder SET wachtwoordhash = NULL, totp_geheim = NULL "
                         "WHERE id = :a")],
                  {"a": anna.id}, lambda: _geladen_en_intrekken(anna.id, passkey.id))
    assert fouten == ["Dit is je enige inlogmethode. Voeg eerst een andere toe."]
    assert db.session.get(Passkey, passkey.id) is not None


# Webroutes


@pytest.fixture
def ingelogd(client, twee):
    anna, geheim, bert = twee
    inloggen(client, geheim)
    return client, anna, bert


@pytest.mark.parametrize("pad", ["/beheerders", "/beheerders/1/blokkeren", "/profiel/intrekken",
                                 "/profiel/wachtwoord", "/profiel/passkey/opties"])
def test_bezoeker_gaat_naar_inloggen(client, pad):
    r = client.post(pad) if pad != "/beheerders" else client.get(pad)
    assert r.status_code == 302 and r.location.endswith("/inloggen")


def test_uitnodigen_toont_link_eenmalig_zonder_flash(ingelogd):
    client, _anna, _bert = ingelogd
    r = client.post("/beheerders", data={"gebruikersnaam": "carla"})
    assert r.status_code == 200 and b"/uitnodiging/" in r.data
    with client.session_transaction() as s:
        assert "_flashes" not in s  # de code staat niet in de leesbare sessiecookie
    assert b"carla" in client.get("/beheerders").data


def test_geblokkeerde_beheerder_verliest_lopende_sessie(app, ingelogd):
    client, anna, bert = ingelogd
    andere = app.test_client()
    inloggen(andere, geheim_van(bert), gebruikersnaam="bert")
    assert andere.get("/rekoverzicht").status_code == 200
    client.post(f"/beheerders/{bert.id}/blokkeren")
    assert andere.get("/rekoverzicht").status_code == 302
    r = client.post(f"/beheerders/{anna.id}/blokkeren", follow_redirects=True)
    assert "altijd een actieve beheerder" in r.text


def geheim_van(b):
    """Het TOTP-geheim van een testbeheerder, ontsleuteld zoals de applicatie het doet."""
    return beheerders._fernet().decrypt(b.totp_geheim).decode()


def test_recente_inlog_vereist(app, ingelogd):
    client, anna, _bert = ingelogd
    met_passkey(anna)
    with client.session_transaction() as s:
        s["ingelogd_op"] = int(time.time()) - 601
    r = client.post("/profiel/intrekken", data={"methode": "wachtwoord"})
    assert r.status_code == 302 and r.location.endswith("/inloggen")
    assert db.session.get(Beheerder, anna.id).wachtwoordhash is not None
    assert client.get("/rekoverzicht").status_code == 302  # opnieuw inloggen
    r = client.post("/profiel/passkey/opties", json={})
    assert r.status_code == 302  # na het wissen van de sessie: niet ingelogd


def test_recente_inlog_json_geeft_401_met_url(app, ingelogd):
    client, _anna, _bert = ingelogd
    with client.session_transaction() as s:
        s["ingelogd_op"] = int(time.time()) - 601
    r = client.post("/profiel/passkey/opties", json={})
    assert r.status_code == 401 and r.json["url"] == "/inloggen"


@pytest.mark.parametrize("pad", ["/beheerders", "/beheerders/{bert}/herstellen",
                                 "/profiel/passkey", "/profiel/wachtwoord"])
def test_recente_inlog_vereist_voor_uitnodigen_herstellen_en_toevoegen(ingelogd, pad):
    """Wie een oudere open sessie overneemt, maakt geen account en neemt er geen over (aegis)."""
    client, _anna, bert = ingelogd
    with client.session_transaction() as s:
        s["ingelogd_op"] = int(time.time()) - 601
    voor = (db.session.scalar(select(db.func.count()).select_from(Uitnodiging)),
            db.session.scalar(select(db.func.count()).select_from(Passkey)))
    r = client.post(pad.format(bert=bert.id), data={"gebruikersnaam": "carla"})
    assert r.status_code == 302 and r.location.endswith("/inloggen")
    assert db.session.scalar(select(Beheerder).where(Beheerder.gebruikersnaam == "carla")) is None
    assert (db.session.scalar(select(db.func.count()).select_from(Uitnodiging)),
            db.session.scalar(select(db.func.count()).select_from(Passkey))) == voor


@pytest.mark.parametrize("actie", ["blokkeren", "deblokkeren", "verwijderen"])
def test_recente_inlog_vereist_voor_blokkeren_deblokkeren_en_verwijderen(ingelogd, actie):
    """Wie een oudere open sessie overneemt, geeft een geblokkeerd account zijn methodes niet
    terug (#12)."""
    client, anna, bert = ingelogd
    if actie == "deblokkeren":
        beheerders.blokkeren(bert.id, actor(anna))
    actief = db.session.get(Beheerder, bert.id).actief
    with client.session_transaction() as s:
        s["ingelogd_op"] = int(time.time()) - 601
    r = client.post(f"/beheerders/{bert.id}/{actie}")
    assert r.status_code == 302 and r.location.endswith("/inloggen")
    db.session.expire_all()
    b = db.session.get(Beheerder, bert.id)
    assert b is not None and b.actief == actief


def test_intrekken_beeindigt_alle_eigen_sessies_niet_die_van_anderen(app, ingelogd):
    client, anna, bert = ingelogd
    met_passkey(anna)
    tweede = app.test_client()
    inloggen(tweede, geheim_van(anna), stappen_verder=2)
    van_bert = app.test_client()
    inloggen(van_bert, geheim_van(bert), gebruikersnaam="bert")
    r = client.post("/profiel/intrekken", data={"methode": "wachtwoord"})
    assert r.location.endswith("/inloggen")
    assert client.get("/rekoverzicht").status_code == 302 and tweede.get("/rekoverzicht").status_code == 302
    assert van_bert.get("/rekoverzicht").status_code == 200


def test_profiel_toont_methodes_en_wachtwoord_toevoegen(app, client):
    anna = beheerders.uitnodiging(beheerders.uitnodigen("anna", CLI)).beheerder
    met_passkey(anna)
    with client.session_transaction() as s:
        s.update(beheerder_id=anna.id, sessieversie=anna.sessieversie,
                 ingelogd_op=int(time.time()))
    r = client.get("/profiel")
    assert b"Passkey 1 intrekken" in r.data and b"Wachtwoord toevoegen" in r.data
    with client.session_transaction() as s:
        geheim = Fernet(app.config["TOTP_SLEUTEL"]).decrypt(s["totp_nieuw"].encode()).decode()
    r = client.post("/profiel/wachtwoord", data={"wachtwoord": WACHTWOORD,
                                                 "herhaling": WACHTWOORD,
                                                 "code": code_bij(geheim)})
    assert r.location.endswith("/profiel")
    assert db.session.get(Beheerder, anna.id).wachtwoordhash is not None
    assert client.get("/rekoverzicht").status_code == 200  # toevoegen laat de sessie staan


def _qr_pad(html):
    return re.search(r'<svg[^>]*class="bl-qr".*? d="([^"]+)"', html, re.DOTALL).group(1)


def _link_en_qr(r):
    html = r.get_data(as_text=True)
    link = re.search(r'<code id="uitnodigingslink">([^<]+)</code>', html).group(1)
    return link, html


@pytest.mark.parametrize("pad", ["/beheerders", "/beheerders/{bert}/herstellen"])
def test_link_toont_qr_naar_dezelfde_link_met_naam_en_zonder_cache(ingelogd, pad):
    client, _anna, bert = ingelogd
    data = {"gebruikersnaam": "carla"} if pad == "/beheerders" else {}
    r = client.post(pad.format(bert=bert.id), data=data)
    link, html = _link_en_qr(r)
    assert "/uitnodiging/" in link
    assert _qr_pad(html) == _qr_pad(segno.make(link, error="m").svg_inline(svgclass="bl-qr"))
    assert re.search(r'<svg role="img" aria-label="QR-code van de uitnodigingslink"', html)
    assert r.headers["Cache-Control"] == "no-store"
    code = link.rsplit("/", 1)[1]
    assert code not in client.get("/beheerders").get_data(as_text=True)
    assert all(code not in str(r.gegevens) for r in db.session.scalars(select(Logregel)))
    with client.session_transaction() as s:
        assert "_flashes" not in s
