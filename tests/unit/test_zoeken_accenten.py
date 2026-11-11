"""Zoeken zonder onderscheid in accenten en hoofdletters (#232), per lijst die boot_of_lid_bevat of
alle_leden gebruikt. Zoekwaarden komen van de beheerder en uit namen van e-boekhouden."""

from datetime import timedelta

import pytest

from app.domein import CLI, boten, indeling, leden, toewijzing, vandaag, wachtlijst
from tests.unit.hulp import lid, plaats
from tests.unit.test_indeling_en_toewijzing import boot, soort
from tests.unit.test_overzichten_en_instellingen import opzeggen

# (zoektekst, naam): elk paar moet vinden, in beide richtingen en met hoofdletters.
PAREN = [("jose", "José"), ("josé", "Jose"), ("JOSÉ", "jose"), ("jose", "JOSÉ"), ("zoë", "Zoe"),
         ("zoe", "Zoë"), ("noel", "Noël"), ("naief", "Naïef"), ("bjorn", "Björn"),
         ("muller", "Müller"), ("MÜLLER", "muller")]
IDS = [f"{zoek}-{naam}" for zoek, naam in PAREN]


@pytest.mark.parametrize(("zoek", "naam"), PAREN, ids=IDS)
def test_leden_vindt_naam_zonder_onderscheid_in_accenten(app, zoek, naam):
    # Mutant: unaccent uit leden.bevat halen valt hier.
    lid("1001", naam)
    lid("1002", "Anders")
    assert [x.naam for x in leden.alle_leden(zoek)] == [naam]


@pytest.mark.parametrize(("zoek", "naam"), PAREN, ids=IDS)
def test_boten_vindt_boot_en_eigenaar_zonder_onderscheid_in_accenten(app, zoek, naam):
    boot(lid("1001", naam).id, naam="Reiger")
    boot(None, naam=naam)  # clubboot: de naam van de boot zelf
    boot(None, naam="Klipper")
    assert {b.naam for b in boten.boten(zoek)} == {"Reiger", naam}


def test_wachtlijst_vindt_boot_en_eigenaar_met_accent(app):
    wachtlijst.erop_zetten(boot(lid("1001", "José").id, naam="Reiger").id, "", CLI)
    wachtlijst.erop_zetten(boot(lid("1002", "Anders").id, naam="Café").id, "", CLI)
    namen = lambda zoek: [w.boot.naam for _s, rij in wachtlijst.lijsten(zoek) for w in rij]
    assert namen("jose") == ["Reiger"] and namen("josé") == ["Reiger"]
    assert namen("cafe") == ["Café"] and namen("CAFÉ") == ["Café"]
    assert namen("zzz") == []


@pytest.fixture
def opzeggers(app):
    for n, (naam, dagen) in enumerate([("José", -30), ("Zoë", 30)]):
        eigenaar = lid(str(n), naam)
        toewijzing.toewijzen(plaats(f"B/1/{n + 1}", [soort("Kajak")]).id,
                             boot(eigenaar.id, naam=f"Boot{n}").id, CLI)
        opzeggen(eigenaar.id, opzegdatum=vandaag() + timedelta(days=dagen))


def test_opgezegd_vindt_oud_lid_met_accent(opzeggers):
    codes = lambda zoek: [p.code for _d, p in indeling.plaatsen_van_oud_leden(zoek)]
    assert codes("jose") == ["B/1/1"] and codes("JOSÉ") == ["B/1/1"] and codes("zoe") == []


def test_gaan_opzeggen_vindt_lid_met_accent(opzeggers):
    codes = lambda zoek: [p.code for p in indeling.plaatsen_van_opzeggende_leden(zoek)]
    assert codes("zoe") == ["B/1/2"] and codes("ZOË") == ["B/1/2"] and codes("jose") == []


@pytest.mark.parametrize("teken", ["%", "_", "\\", "\uff05", "\uff3f", "\uff3c"],
                         ids=["procent", "streepje", "backslash", "breed-procent", "breed-streepje",
                              "brede-backslash"])
def test_procent_liggend_streepje_en_backslash_blijven_letterlijk(app, teken):
    # Mutant: de escape in leden.bevat weghalen laat '%' en '_' alles vinden; de escape vóór
    # unaccent laat de brede tekens (％ ＿ ＼), die unaccent omzet, alles vinden (AEG-01).
    lid("1001", "José")
    assert leden.alle_leden(teken) == []
    lid("1002", f"Piet {teken}ex")
    assert [x.naam for x in leden.alle_leden(teken)] == [f"Piet {teken}ex"]
