"""Het aantal boten per lid op /leden (#400): alle boten van het lid, in één query."""

from sqlalchemy import event

from app.domein import CLI, leden, toewijzing, wachtlijst
from app.models import db
from tests.unit.hulp import lid, plaats
from tests.unit.test_indeling_en_toewijzing import boot
from tests.unit.test_web_beheer import ingelogd  # noqa: F401


def aantallen(zoek=""):
    return {x.naam: x.aantal_boten for x in leden.alle_leden(zoek)}


def test_aantal_telt_alle_boten_van_het_lid_en_niet_die_van_anderen(app):
    # Mutant: join in plaats van subquery laat het lid zonder boten weg; filter op plaats telt te weinig.
    lid("1", "Nul")
    een, vier = lid("2", "Een"), lid("3", "Vier")
    boot(een.id, naam="B1")
    boot(vier.id, naam="M1")  # zonder plaats
    toewijzing.toewijzen(plaats("A/1/1").id, boot(vier.id, naam="M2").id, CLI)  # met plaats
    wachtlijst.erop_zetten(boot(vier.id, naam="M3").id, "", CLI)  # op de wachtlijst
    boot(vier.id, naam="M4")
    boot(None, naam="Club")  # clubboot: geen lid
    boot(None, naam="Onbekend", onbekend=True)  # geen eigenaar: geen lid
    assert aantallen() == {"Nul": 0, "Een": 1, "Vier": 4}


def test_aantal_blijft_kloppen_bij_zoeken(app):
    boot(lid("1", "Anna").id, naam="B1")
    lid("2", "Bert")
    assert aantallen("anna") == {"Anna": 1}


def test_een_query_voor_de_hele_lijst(app):
    for i in range(6):
        boot(lid(f"20{i}", f"Lid {i}").id, naam=f"Boot {i}")
    db.session.expire_all()
    regels = []
    teller = lambda *a: regels.append(1)
    event.listen(db.engine, "before_cursor_execute", teller)
    try:
        assert [x.aantal_boten for x in leden.alle_leden()] == [1] * 6
    finally:
        event.remove(db.engine, "before_cursor_execute", teller)
    assert len(regels) == 1  # mutant: een telling per lid geeft 7


def test_leden_pagina_toont_aantal_na_de_link(ingelogd):  # noqa: F811
    # Mutant: de tekst in de link zetten maakt de linknaam "Vier (4 boten)"; enkelvoud/meervoud vallen op "1 boten".
    lid("1", "Nul")
    boot(lid("2", "Een").id, naam="B1")
    html = ingelogd.get("/leden").text
    assert ">Nul</a> <span data-label=\"Aantal boten\">(0 boten)</span>" in html
    assert ">Een</a> <span data-label=\"Aantal boten\">(1 boot)</span>" in html
