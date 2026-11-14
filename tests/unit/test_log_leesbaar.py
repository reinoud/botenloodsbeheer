"""Leesbaar log (#174, BV-82): actie en verwijzing als tekst; het technische log, de opslag en de
gegevens blijven ongewijzigd. Namen zijn gebruikersinvoer en blijven geëscapet."""

import pytest
from sqlalchemy import event

from app.domein import CLI, boten, indeling, log, toewijzing, tokens
from app.models import Bootsoort, Logregel, Token, db
from tests.unit.hulp import beheerder_met_wachtwoord, lid, plaats
from tests.unit.test_blok3a_lijsten import GEESCAPET, XSS, ingelogd  # noqa: F401

REK_XSS, REK_GEESCAPET = "<b>x", "&lt;b&gt;x"


@pytest.mark.parametrize("opgeslagen,tekst", [
    ("plaats.toegewezen", "plaats toegewezen"),
    ("boot.foto_vervangen", "boot foto vervangen"),
    ("beheerder.methode_ingesteld", "beheerder methode ingesteld"),
    # onbekend: ongewijzigd
    ("boot.nieuw_soort", "boot.nieuw_soort"),
    ("Onbekend", "Onbekend"),
])
def test_actietekst(opgeslagen, tekst):
    # Mutant: de bekend-controle weglaten valt op "boot nieuw soort".
    assert log.actietekst(opgeslagen) == tekst


def _regel(*verwijzingen):
    return Logregel(verwijzingen=list(verwijzingen))


def test_betreft_noemt_elke_soort_en_laat_onbekende_of_verwijderde_staan(app):
    p = plaats("A/1/1")
    eigenaar = lid(naam="Anna de Vries", lidnummer="1001")
    b = boten.boot_aanmaken("Zeemeeuw", 1, eigenaar.id, None, CLI)
    verwijzingen = [f"plaats:{p.id}", f"rek:{p.rek_id}", f"boot:{b.id}", f"lid:{eigenaar.id}",
                    "bootsoort:1", "boot:99999", "taakrun:5", "instelling:huisstijl", "clubboot",
                    "lid:x", "plaats:99999999999"]
    tekst = log.betreft(verwijzingen, log.namen([_regel(*verwijzingen)]))
    soort = db.session.get(Bootsoort, 1).naam
    assert tekst == (f"Plaats A/1/1, Rek A, Boot Zeemeeuw, Lid Anna de Vries (1001), Bootsoort {soort}, "
                     "boot:99999, taakrun:5, instelling:huisstijl, clubboot, lid:x, plaats:99999999999")


def test_beheerder_en_token_in_betreft(app):
    anna, _ = beheerder_met_wachtwoord("anna")
    tokens.robot_maken("koppeling", ["boten:lezen"], ["192.0.2.1"], None, CLI)
    token = db.session.scalar(db.select(Token))
    verwijzingen = [f"beheerder:{anna.id}", f"token:{token.id}"]
    assert log.betreft(verwijzingen, log.namen([_regel(*verwijzingen)])) == f"Beheerder {anna.naam}, Token koppeling"


@pytest.mark.parametrize("naam,tekst", [
    ("B", "Rek B"), ("Rek B", "Rek B"), ("rek b", "rek b"), ("Rek", "Rek"), ("Reken", "Rek Reken")])
def test_rek_krijgt_geen_dubbel_rek(app, naam, tekst):
    # Mutant: altijd "Rek " ervoor zetten valt op "Rek B", "rek b" en "Rek".
    r = indeling.rek_aanmaken(naam, "", {(1, 1)}, CLI)
    assert log.betreft([f"rek:{r.id}"], log.namen([_regel(f"rek:{r.id}")])) == tekst


def test_een_pagina_haalt_namen_per_soort_in_een_query_op(app):
    p = plaats("A/1/1")
    regels = []
    for i in range(6):
        eigenaar = lid(lidnummer=f"20{i}", naam=f"Lid {i}")
        b = boten.boot_aanmaken(f"Boot {i}", 1, eigenaar.id, None, CLI)
        regels.append(_regel(f"plaats:{p.id}", f"rek:{p.rek_id}", f"boot:{b.id}", f"lid:{eigenaar.id}"))
    aantal = []
    teller = lambda *a: aantal.append(1)
    event.listen(db.engine, "before_cursor_execute", teller)
    try:
        log.namen(regels)
    finally:
        event.remove(db.engine, "before_cursor_execute", teller)
    assert len(aantal) == 4  # plaats, rek, boot, lid: niet 24 (mutant: per regel opvragen)


def test_log_toont_leesbare_tekst_en_escapet_namen(ingelogd):  # noqa: F811
    # Mutant: |safe op de betreft-tekst valt op de eerste assert (rauwe <b>).
    p = plaats("A/1/1")
    eigenaar = lid(naam=XSS)
    b = boten.boot_aanmaken(XSS, 1, eigenaar.id, None, CLI)
    toewijzing.toewijzen(p.id, b.id, CLI)
    indeling.rek_wijzigen(p.rek_id, REK_XSS, "", CLI)  # een reknaam mag geen / bevatten, dus geen </b>
    for pad in ("/log", f"/boten/{b.id}", f"/plaatsen/{p.id}"):
        tekst = ingelogd.get(pad).text
        assert XSS not in tekst and REK_XSS not in tekst, pad
        assert (f'<span class="bl-logactie">plaats toegewezen</span> <span class="bl-logbetreft">Plaats {REK_GEESCAPET}/1/1, '
                f'Rek {REK_GEESCAPET}, Boot {GEESCAPET}, Lid {GEESCAPET} (1001)</span>') in tekst, pad


def test_technisch_log_toont_opgeslagen_actie_en_verwijzing(ingelogd):  # noqa: F811
    r = indeling.rek_aanmaken("B", "", {(1, 1)}, CLI)
    tekst = ingelogd.get("/log/techniek").text
    assert (f'<span class="bl-logactie">rek.aangemaakt</span> <span class="bl-logbetreft">rek:{r.id}</span>'
            in tekst)


def test_gegevens_blijven_zoals_opgeslagen(ingelogd):  # noqa: F811
    # BV-82 punt 4: alleen betreft wordt leesbaar; een mutant die namen ook in de gegevens zet, valt hier
    anna, bert = lid(naam="Anna de Vries", lidnummer="1001"), lid(naam="Bert Jansen", lidnummer="1002")
    b = boten.boot_aanmaken("Zeemeeuw", 1, anna.id, None, CLI)
    ingelogd.post(f"/boten/{b.id}", data={"naam": "Zeemeeuw", "bootsoort": "1", "eigenaar": str(bert.id)})
    assert f"eigenaar: [&#39;lid:{anna.id}&#39;, &#39;lid:{bert.id}&#39;]" in ingelogd.get("/log").text
