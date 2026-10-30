"""Ledensynchronisatie met de stub als nepbron (BLB-006, BLB-007, ADR-004) en de taak in de
worker (ADR-007)."""

import json
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select

from app import taken
from app.domein import CLI, LEDENSYNCHRONISATIE, Regelfout, leden
from app.ledenbron import LedenbronFout, StubBron
from app.models import Lid, Logregel, Taakrun, db


def record(nummer, **velden):
    return {"lidnummer": nummer, "naam": f"Lid {nummer}", "adres": "Proefweg 1",
            "telefoon": "06-00000000", "email": f"{nummer}@example.org",
            "lid_sinds": "2020-01-01", "opzegdatum": None} | velden


@pytest.fixture
def bron(tmp_path):
    """Schrijft records naar een nieuw stubbestand en geeft de bron terug."""
    def maak(records):
        pad = tmp_path / "leden.json"
        pad.write_text(records if isinstance(records, str) else json.dumps(records))
        return StubBron(str(pad))
    return maak


def sync(bron):
    aantallen = leden.synchroniseer(bron, LEDENSYNCHRONISATIE)
    db.session.commit()
    return aantallen


def alle():
    return {lid.lidnummer: lid for lid in db.session.scalars(select(Lid))}


def test_nieuwe_en_gewijzigde_leden_op_lidnummer(app, bron):
    sync(bron([record("1"), record("2")]))
    aantallen = sync(bron([record("1", adres="Nieuweweg 2"), record("2"), record("3")]))
    assert aantallen | {"ontvangen": 0} == {"ontvangen": 0, "nieuw": 1, "bijgewerkt": 1,
                                           "uit_bron": 0, "ongeldig": 0, "overgeslagen": 0}
    lid = alle()["1"]
    assert (lid.adres, lid.email, lid.lid_sinds) == ("Nieuweweg 2", "1@example.org",
                                                     date(2020, 1, 1))


def test_log_noemt_velden_zonder_waarden(app, bron):
    sync(bron([record("1")]))
    sync(bron([record("1", adres="Geheimstraat 9", telefoon="06-99999999")]))
    regels = db.session.scalars(select(Logregel).order_by(Logregel.id)).all()
    assert [r.actie for r in regels] == ["lid.aangemaakt", "leden.gesynchroniseerd",
                                         "lid.bijgewerkt", "leden.gesynchroniseerd"]
    assert regels[2].gegevens == {"velden": ["adres", "telefoon"]}
    assert regels[2].actor_soort == "taak"
    tekst = json.dumps([(r.gegevens, r.verwijzingen) for r in regels])
    for waarde in ("Geheimstraat", "06-", "@example.org", "Lid 1"):
        assert waarde not in tekst


def test_ongeldige_records_overgeslagen_rest_verwerkt(app, bron):
    sync(bron([record("1"), record("2")]))
    aantallen = sync(bron([
        record("1", email="geen-adres"),  # bestaand lid met tikfout: blijft lid, ongewijzigd
        record("2"), record(None), {"naam": "Zonder nummer"}, record(""), record("4", naam=" "),
        record("5", lid_sinds="31-12-2020"), record("6", naam=7), "geen record", record("2"),
        record("7", naam="x" * 300),
    ]))
    assert aantallen["ongeldig"] == 9 and aantallen["nieuw"] == 1 and aantallen["uit_bron"] == 0
    lid = alle()
    assert lid["1"].email == "1@example.org" and lid["1"].uit_bron_op is None
    assert set(lid) == {"1", "2", "7"} and len(lid["7"].naam) == 100


def test_ontbrekend_lid_wordt_oud_lid_en_komt_terug(app, bron):
    sync(bron([record("1"), record("2")]))
    assert sync(bron([record("1"), record("3")]))["uit_bron"] == 1
    assert alle()["2"].uit_bron_op is not None and leden.is_oud_lid(alle()["2"])
    sync(bron([record("1"), record("2"), record("3")]))
    assert alle()["2"].uit_bron_op is None


def test_halve_lijst_breekt_af_zonder_wijziging(app, bron):
    sync(bron([record(str(n)) for n in range(1, 11)]))
    with pytest.raises(LedenbronFout, match="minder dan de helft"):
        leden.synchroniseer(bron([record(str(n)) for n in range(1, 5)]), LEDENSYNCHRONISATIE)
    db.session.rollback()
    assert all(lid.uit_bron_op is None for lid in alle().values())
    # Precies de helft gaat wel door.
    assert sync(bron([record(str(n)) for n in range(1, 6)]))["uit_bron"] == 5


@pytest.mark.parametrize("inhoud", ["{kapot", '{"geen": "lijst"}'])
def test_onleesbare_bron(app, bron, inhoud):
    with pytest.raises(LedenbronFout, match="onleesbaar"):
        bron(inhoud).haal_leden()


def test_opgeschoond_oud_lid_komt_niet_terug(app, bron):
    lang_geleden = (date.today() - timedelta(days=5 * 366)).isoformat()
    aantallen = sync(bron([record("1"), record("2", opzegdatum=lang_geleden)]))
    assert aantallen["overgeslagen"] == 1 and set(alle()) == {"1"}


def test_jaren_terug_op_schrikkeldag():
    assert leden.jaren_terug(date(2028, 2, 29), 5) == date(2023, 2, 28)


def test_terugschrijven_niet_beschikbaar():
    bron = StubBron("x")
    assert not bron.kan_terugschrijven
    with pytest.raises(Exception, match="niet beschikbaar"):
        bron.schrijf_bootaantallen({})


# Taak in de worker


def test_aanvraag_wordt_door_de_worker_uitgevoerd(app):
    leden.synchronisatie_aanvragen(CLI)
    with pytest.raises(Regelfout, match="al een synchronisatie"):
        leden.synchronisatie_aanvragen(CLI)
    taken.ronde()
    run = db.session.scalar(select(Taakrun).where(Taakrun.taak == leden.TAAK))
    assert run.status == "geslaagd" and run.aantallen["nieuw"] == 208
    assert len(alle()) == 208  # de fixture: 210, waarvan 2 langer dan 5 jaar opgezegd


def test_mislukte_synchronisatie_in_taakrun_en_log(app, bron):
    app.config["LEDENBRON_STUB_BESTAND"] = "/bestaat/niet.json"
    leden.synchronisatie_aanvragen(CLI)
    taken.ronde()
    run = db.session.scalar(select(Taakrun).where(Taakrun.taak == leden.TAAK))
    assert (run.status, run.foutmelding) == ("mislukt", "De ledenbron is niet bereikbaar.")
    regel = db.session.scalars(select(Logregel).order_by(Logregel.id.desc())).first()
    assert regel.actie == "leden.synchronisatie_mislukt"
    assert alle() == {}


def test_zonder_bron_verandert_er_niets(app):
    app.config["LEDENBRON"] = ""
    taken.synchroniseer(Taakrun(taak=leden.TAAK, status="bezig"))
    run = db.session.scalar(select(Taakrun).where(Taakrun.taak == leden.TAAK))
    assert (run.status, run.foutmelding) == ("mislukt", "Er is geen ledenbron ingesteld.")
    assert alle() == {}


def test_onverwachte_fout_zonder_inhoud_in_taakrun(app, monkeypatch):
    def kapot(*_):
        raise ValueError("adres van iemand")
    monkeypatch.setattr(leden, "synchroniseer", kapot)
    taken.synchroniseer(Taakrun(taak=leden.TAAK, status="bezig"))
    run = db.session.scalar(select(Taakrun).where(Taakrun.taak == leden.TAAK))
    assert run.foutmelding == "Onverwachte fout (ValueError)."


def test_planning_dagelijks_na_tijdstip_met_wachttijd_na_fout(app):
    app.config["SYNC_TIJDSTIP"] = datetime.strptime("03:00", "%H:%M").time()
    ochtend = datetime.now(UTC).replace(hour=9, minute=0)  # 10:00 of 11:00 in Amsterdam
    assert not taken.sync_gepland(ochtend.replace(hour=0))  # 01:00 of 02:00: te vroeg
    assert taken.sync_gepland(ochtend)
    db.session.add(Taakrun(taak=leden.TAAK, status="mislukt", gestart_op=ochtend))
    db.session.commit()
    assert not taken.sync_gepland(ochtend + timedelta(minutes=30))
    assert taken.sync_gepland(ochtend + timedelta(minutes=61))
    db.session.add(Taakrun(taak=leden.TAAK, status="geslaagd", gestart_op=ochtend))
    db.session.commit()
    assert not taken.sync_gepland(ochtend + timedelta(hours=3))
