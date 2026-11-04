"""Boot wijzigen: naam, bootsoort en eigenaar (BLB-005, issue #39). Een wijziging geeft één
logregel boot.gewijzigd met alleen de gewijzigde velden; een weigering of gelijke invoer geen."""

from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.domein import CLI, Regelfout, boten, log, toewijzing
from app.models import Boot, Logregel, db
from tests.unit.hulp import lid, race
from tests.unit.test_indeling_en_toewijzing import acties, boot, plaats, soort


def wijzig(b, naam=None, bootsoort="Kajak", lid_id=..., actor=CLI):
    return boten.boot_wijzigen(b.id, b.naam if naam is None else naam, soort(bootsoort),
                               b.lid_id if lid_id is ... else lid_id, actor)


def regels():
    return db.session.scalars(select(Logregel).where(Logregel.actie == "boot.gewijzigd")).all()


# Validatie, zoals boot_aanmaken


@pytest.mark.parametrize("naam", ["", "   ", "x" * 101], ids=["leeg", "spaties", "101_tekens"])
def test_ongeldige_naam_geweigerd(app, naam):
    b = boot(lid().id)
    with pytest.raises(Regelfout, match="naam van 1 tot 100 tekens"):
        wijzig(b, naam=naam)
    assert db.session.get(Boot, b.id).naam == "Zeemeeuw" and not regels()


@pytest.mark.parametrize("naam", ["x", "x" * 100, "  Fuut  "], ids=["1_teken", "100_tekens", "getrimd"])
def test_geldige_naam_gewijzigd(app, naam):
    b = boot(lid().id)
    wijzig(b, naam=naam)
    assert db.session.get(Boot, b.id).naam == naam.strip()


def test_onbekende_bootsoort_en_geen_bootsoort_geweigerd(app):
    b = boot(lid().id)
    for kies in (9999, None):
        with pytest.raises(Regelfout, match="Kies een bootsoort"):
            boten.boot_wijzigen(b.id, "Fuut", kies, b.lid_id, CLI)
    assert not regels()


def test_onbekend_lid_en_onbekende_boot_geweigerd(app):
    b = boot(lid().id)
    with pytest.raises(Regelfout, match="Dit lid bestaat niet"):
        wijzig(b, lid_id=9999)
    with pytest.raises(Regelfout, match="Deze boot bestaat niet"):
        boten.boot_wijzigen(b.id + 99, "Fuut", soort("Kajak"), None, CLI)
    assert not regels()


@pytest.mark.parametrize("veld", ["opzegdatum", "uit_bron_op"])
def test_oud_lid_wordt_geen_nieuwe_eigenaar_maar_blijft_eigenaar(app, veld):
    oud = lid("2001", "Oud Lid", **{veld: date.today() - timedelta(days=1)})
    nieuw = lid("2002", "Nieuw Lid")
    b = Boot(naam="Zeemeeuw", bootsoort_id=soort("Kajak"), lid_id=oud.id)  # van vóór de opzegging
    db.session.add(b)
    db.session.commit()
    wijzig(b, naam="Fuut")  # eigenaar wijzigt niet: een oud-lid mag blijven staan
    assert db.session.get(Boot, b.id).lid_id == oud.id
    c = boot(nieuw.id, naam="Kievit")
    with pytest.raises(Regelfout, match="is oud-lid en krijgt geen nieuwe boot"):
        wijzig(c, lid_id=oud.id)
    assert db.session.get(Boot, c.id).lid_id == nieuw.id
    wijzig(b, lid_id=nieuw.id)  # van een oud-lid af naar een actief lid mag
    assert db.session.get(Boot, b.id).lid_id == nieuw.id


# Boot met een plaats


def test_bootsoort_die_de_plaats_niet_past_geweigerd(app):
    p = plaats(soorten=("Kajak", "Surfski"))
    b = boot(lid().id)
    toewijzing.toewijzen(p.id, b.id, CLI)
    with pytest.raises(Regelfout, match="Plaats A/1/1 is niet geschikt voor een c11"):
        wijzig(b, bootsoort="C11")
    assert db.session.get(Boot, b.id).bootsoort.naam == "Kajak" and not regels()


def test_bootsoort_die_de_plaats_past_gewijzigd(app):
    p = plaats(soorten=("Kajak", "Surfski"))
    b = boot(lid().id)
    toewijzing.toewijzen(p.id, b.id, CLI)
    wijzig(b, bootsoort="Surfski")
    assert db.session.get(Boot, b.id).bootsoort.naam == "Surfski"


def test_lid_naar_clubboot_op_gewone_plaats_geweigerd(app):
    p = plaats()
    b = boot(lid().id)
    toewijzing.toewijzen(p.id, b.id, CLI)
    with pytest.raises(Regelfout, match="is een clubboot en hoort op een clubplaats"):
        wijzig(b, lid_id=None)
    assert db.session.get(Boot, b.id).lid_id is not None


def test_clubboot_naar_lid_op_clubplaats_geweigerd(app):
    p = plaats(club=True)
    b = boot(None)
    toewijzing.toewijzen(p.id, b.id, CLI)
    with pytest.raises(Regelfout, match="is een clubplaats en alleen voor clubboten"):
        wijzig(b, lid_id=lid().id)
    assert db.session.get(Boot, b.id).lid_id is None


def test_ander_lid_op_plaats_en_wissel_zonder_plaats_mag(app):
    p = plaats()
    anna, bert = lid(), lid("1002", "Bert Jansen")
    b, zonder = boot(anna.id), boot(anna.id, naam="Fuut")
    toewijzing.toewijzen(p.id, b.id, CLI)
    wijzig(b, lid_id=bert.id)  # lid naar lid op een gewone plaats
    wijzig(zonder, bootsoort="C11", lid_id=None)  # zonder plaats: vrije wissel
    assert db.session.get(Boot, b.id).lid_id == bert.id
    assert db.session.get(Boot, zonder.id).lid_id is None


# Log


def test_zonder_verschil_geen_logregel(app):
    b = boot(lid().id)
    assert wijzig(b).id == b.id
    assert acties() == ["boot.aangemaakt"]


def test_naam_en_bootsoort_in_het_log_met_oud_en_nieuw(app):
    anna = lid()
    b = boot(anna.id)
    wijzig(b, naam="Fuut", bootsoort="Surfski")
    (r,) = regels()
    assert r.gegevens == {"naam": ["Zeemeeuw", "Fuut"], "bootsoort": ["Kajak", "Surfski"]}
    assert r.verwijzingen == [f"boot:{b.id}", f"lid:{anna.id}"]
    assert r.actor_naam == "cli"


def test_alleen_gewijzigde_velden_in_het_log(app):
    b = boot(lid().id)
    wijzig(b, naam="Fuut")
    assert regels()[0].gegevens == {"naam": ["Zeemeeuw", "Fuut"]}


def test_eigenaarwissel_logt_geen_persoonsgegevens_en_beide_leden(app):
    anna, bert = lid(), lid("1002", "Bert Jansen")
    b = boot(anna.id)
    wijzig(b, lid_id=bert.id)
    (r,) = regels()
    assert r.gegevens == {"eigenaar": [f"lid:{anna.id}", f"lid:{bert.id}"]}
    assert r.verwijzingen == [f"boot:{b.id}", f"lid:{anna.id}", f"lid:{bert.id}"]
    for deel in (anna.naam, bert.naam, anna.email, bert.lidnummer):
        assert deel not in str((r.gegevens, r.verwijzingen))
    for betrokken in (anna, bert):
        assert r.id in [x.id for x in log.regels([f"lid:{betrokken.id}"])]


def test_clubboot_wissel_verwijst_alleen_naar_het_lid(app):
    anna = lid()
    b = boot(None)
    wijzig(b, lid_id=anna.id)
    assert regels()[0].verwijzingen == [f"boot:{b.id}", f"lid:{anna.id}"]


def test_boot_wijzigen_staat_bij_de_bootmutaties_en_niet_technisch(app):
    b = boot(lid().id)
    wijzig(b, naam="Fuut")
    assert next(r.actie for r in log.regels([f"boot:{b.id}"])) == "boot.gewijzigd"
    assert "boot.gewijzigd" not in [r.actie for r in log.regels(technisch=True)]


# Gelijktijdig (ADR-003): de boot wordt eerst vergrendeld, dan de plaats van de boot. Zonder het
# bootslot ziet de tweede sessie een toewijzing niet die nog niet is gecommit; zonder het
# plaatsslot leest ze de bootsoorten van de plaats voor een gelijktijdige wijziging.

BOOTSLOT = "SELECT id FROM boot WHERE id = :b FOR UPDATE"
PLAATSSLOT = "SELECT id FROM plaats WHERE id = :p FOR UPDATE"


def test_gelijktijdig_toewijzen_en_boot_wijzigen(app):
    p = plaats(soorten=("Kajak",))
    b = boot(lid().id)
    fouten = race(app, [BOOTSLOT, "UPDATE plaats SET boot_id = :b WHERE id = :p"],
                  {"p": p.id, "b": b.id}, lambda: wijzig(b, bootsoort="C11"))
    assert len(fouten) == 1 and "Plaats A/1/1 is niet geschikt voor een c11" in fouten[0]
    assert db.session.get(Boot, b.id).bootsoort.naam == "Kajak" and not regels()


def test_gelijktijdig_plaats_wijzigen_en_boot_wijzigen(app):
    p = plaats(soorten=("Kajak", "Surfski"))
    b = boot(lid().id)
    toewijzing.toewijzen(p.id, b.id, CLI)
    fouten = race(app, [PLAATSSLOT, ("DELETE FROM plaats_bootsoort WHERE plaats_id = :p "
                                    "AND bootsoort_id = :s")],
                  {"p": p.id, "b": b.id, "s": soort("Surfski")},
                  lambda: wijzig(b, bootsoort="Surfski"))
    assert len(fouten) == 1 and "niet geschikt voor een surfski" in fouten[0]
    assert db.session.get(Boot, b.id).bootsoort.naam == "Kajak" and not regels()
