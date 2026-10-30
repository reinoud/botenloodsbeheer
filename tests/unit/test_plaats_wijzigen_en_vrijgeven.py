"""Plaats wijzigen: bootsoorten, clubplaats en code (BLB-002, 003, 004), en vrijgeven
(BLB-011). Elke mutatie geeft een logregel, een weigering geen (ADR-006)."""

import pytest
from sqlalchemy import select

from app.domein import CLI, Regelfout, indeling, log, toewijzing
from app.models import Boot, Logregel, Plaats, db
from tests.unit.hulp import lid, race
from tests.unit.test_indeling_en_toewijzing import acties, boot, plaats, soort


def wijzig(p, code=None, soorten=None, club=None):
    return indeling.plaats_wijzigen(
        p.id, code or p.code, [soort(s) for s in soorten] if soorten else
        [s.id for s in p.bootsoorten], p.is_clubplaats if club is None else club, CLI)


def bezet(soorten=("Kajak", "Surfski"), club=False):
    p = plaats(soorten=soorten, club=club)
    b = boot(None if club else lid().id)
    toewijzing.toewijzen(p.id, b.id, CLI)
    return p, b


def laatste():
    return db.session.scalars(select(Logregel).order_by(Logregel.id.desc())).first()


# BLB-002


def test_bootsoorten_wijzigen_en_loggen(app):
    p = plaats(soorten=("Kajak",))
    wijzig(p, soorten=("Kajak", "C11"))
    assert [s.naam for s in db.session.get(Plaats, p.id).bootsoorten] == ["Kajak", "C11"]
    assert laatste().actie == "plaats.gewijzigd"
    assert laatste().gegevens == {"bootsoorten": [["Kajak"], ["Kajak", "C11"]]}


def test_soort_van_de_boot_weghalen_geweigerd_met_naam_van_de_boot(app):
    p, _b = bezet()
    voor = len(acties())
    with pytest.raises(Regelfout, match="Op plaats A01 ligt Zeemeeuw, een kajak"):
        wijzig(p, soorten=("Surfski",))
    assert len(acties()) == voor
    assert [s.naam for s in db.session.get(Plaats, p.id).bootsoorten] == ["Kajak", "Surfski"]
    wijzig(p, soorten=("Kajak",))  # een andere soort weghalen mag wel


def test_zonder_bootsoort_geweigerd(app):
    p = plaats()
    with pytest.raises(Regelfout, match="minstens één bootsoort"):
        indeling.plaats_wijzigen(p.id, "A01", [], False, CLI)


# BLB-003


def test_clubplaats_markeren_en_dan_alleen_clubboot(app):
    p = plaats()
    wijzig(p, club=True)
    assert laatste().gegevens == {"clubplaats": [False, True]}
    with pytest.raises(Regelfout, match="is een clubplaats en alleen voor clubboten"):
        toewijzing.toewijzen(p.id, boot(lid().id).id, CLI)
    toewijzing.toewijzen(p.id, boot(naam="Clubkajak").id, CLI)


@pytest.mark.parametrize("club", [False, True])
def test_clubplaats_wijzigen_op_bezette_plaats_geweigerd(app, club):
    p, _b = bezet(club=club)
    with pytest.raises(Regelfout, match="Geef de plaats eerst vrij"):
        wijzig(p, club=not club)
    assert db.session.get(Plaats, p.id).is_clubplaats is club


# BLB-004


def test_code_wijzigen_houdt_toewijzing_en_publieke_sleutel(app):
    p, b = bezet()
    sleutel = p.publieke_sleutel
    wijzig(p, code="B07")
    p = db.session.get(Plaats, p.id)
    assert p.code == "B07" and p.boot_id == b.id and p.publieke_sleutel == sleutel
    assert indeling.openbaar(sleutel)["code"] == "B07"
    assert laatste().gegevens == {"plaatscode": ["A01", "B07"]}


def test_code_van_een_andere_plaats_geweigerd(app):
    p = plaats()
    plaats("A02", rek=p.rek)
    with pytest.raises(Regelfout, match="De code a02 hoort al bij een andere plaats"):
        wijzig(p, code="a02")
    assert db.session.get(Plaats, p.id).code == "A01"


def test_ongeldige_code_geweigerd(app):
    p = plaats()
    with pytest.raises(Regelfout, match="1 tot 20 tekens"):
        wijzig(p, code="!" * 3)


def test_niets_gewijzigd_geeft_geen_logregel(app):
    p = plaats()
    voor = len(acties())
    wijzig(p)
    assert len(acties()) == voor


# BLB-011


def test_vrijgeven_boot_blijft_zonder_plaats(app):
    p, b = bezet()
    toewijzing.vrijgeven(p.id, CLI)
    assert db.session.get(Plaats, p.id).boot_id is None
    assert db.session.get(Boot, b.id).plaats is None
    r = laatste()
    assert r.actie == "plaats.vrijgegeven" and r.gegevens == {"plaats": "A01", "boot": "Zeemeeuw"}
    assert {f"plaats:{p.id}", f"boot:{b.id}", f"lid:{b.lid_id}"} <= set(r.verwijzingen)
    # Daarna is de plaats weer toe te wijzen; de applicatie doet dat niet zelf.
    assert log.regels([f"plaats:{p.id}"])[0].actie == "plaats.vrijgegeven"
    toewijzing.toewijzen(p.id, b.id, CLI)


def test_vrije_plaats_vrijgeven_geweigerd(app):
    p = plaats()
    with pytest.raises(Regelfout, match="al vrij"):
        toewijzing.vrijgeven(p.id, CLI)
    with pytest.raises(Regelfout, match="bestaat niet"):
        toewijzing.vrijgeven(p.id + 99, CLI)


# Gelijktijdig: elke functie leest de plaats met FOR UPDATE (ADR-003). Zonder vergrendeling
# leest de tweede sessie de oude toestand en slaagt ze waar ze moet weigeren.

VERGRENDEL = "SELECT id FROM plaats WHERE id = :p FOR UPDATE"


@pytest.mark.parametrize("geval", ["clubplaats", "bootsoort"])
def test_gelijktijdig_toewijzen_en_plaats_wijzigen(app, geval):
    p = plaats(soorten=("Kajak", "Surfski"))
    b = boot(lid().id)
    fouten = race(app, [VERGRENDEL, "UPDATE plaats SET boot_id = :b WHERE id = :p"],
                  {"p": p.id, "b": b.id},
                  lambda: indeling.plaats_wijzigen(
                      p.id, "A01", [soort("Kajak" if geval == "clubplaats" else "Surfski")],
                      geval == "clubplaats", CLI))
    assert len(fouten) == 1 and "Op plaats A01 ligt Zeemeeuw" in fouten[0]
    p = db.session.get(Plaats, p.id)
    assert not p.is_clubplaats and len(p.bootsoorten) == 2


def test_gelijktijdig_vrijgeven(app):
    p, _b = bezet()
    fouten = race(app, [VERGRENDEL, "UPDATE plaats SET boot_id = NULL WHERE id = :p"],
                  {"p": p.id}, lambda: toewijzing.vrijgeven(p.id, CLI))
    assert fouten == ["Deze plaats is al vrij."]
    assert "plaats.vrijgegeven" not in acties()
