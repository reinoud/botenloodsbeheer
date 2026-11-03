"""Bootsoorten beheren (BLB-028): toevoegen, hernoemen en verwijderen, met de weigeringen en de
twee races (verwijderen tegen een nieuwe boot of plaats, en twee gelijktijdige hernoemingen)."""

import io
import time

import pytest
from openpyxl import load_workbook
from sqlalchemy import select, text

from app.domein import CLI, Regelfout, boten, indeling, toewijzing, uitlezen, wachtlijst
from app.models import Bootsoort, Logregel, db
from tests.unit.hulp import lid, race
from tests.unit.test_web_beheer import ingelogd  # noqa: F401  fixture


def soort(naam):
    return next(s for s in indeling.bootsoorten() if s.naam == naam)


def regels(actie):
    return db.session.scalars(select(Logregel).where(Logregel.actie == actie)).all()


def plaats(soort_id, code="A01"):
    rek = indeling.rek_aanmaken("Rek A", CLI)
    return indeling.plaats_aanmaken(rek.id, code, [soort_id], False, CLI)


# Criterium 1: toevoegen


def test_toegevoegde_soort_te_kiezen_bij_boot_en_plaats_met_eigen_wachtlijst(app):
    s = indeling.bootsoort_toevoegen("  Waterfiets ", CLI)
    assert s.naam == "Waterfiets"
    assert indeling.bootsoorten()[-1].id == s.id  # volgorde op id
    p = plaats(s.id)
    b = boten.boot_aanmaken("Pedaalpiet", s.id, lid().id, None, CLI)
    assert p.bootsoorten == [s] and b.bootsoort == s
    assert [x.id for x in indeling.vrije_plaatsen(s.id)] == [p.id]
    wachtlijst.erop_zetten(b.id, None, CLI)
    assert [(k.naam, [w.boot.naam for w in rij]) for k, rij in wachtlijst.lijsten()] == [
        ("Waterfiets", ["Pedaalpiet"])]
    [r] = regels("bootsoort.toegevoegd")
    assert r.verwijzingen == [f"bootsoort:{s.id}"] and r.gegevens == {"naam": "Waterfiets"}


@pytest.mark.parametrize("naam, melding", [
    ("", "1 tot 50 tekens"),
    ("   ", "1 tot 50 tekens"),
    ("x" * 51, "1 tot 50 tekens"),
    ("kAJAK", "De bootsoort Kajak bestaat al"),
], ids=["leeg", "spaties", "51-tekens", "andere-hoofdletters"])
def test_toevoegen_geweigerd(app, naam, melding):
    with pytest.raises(Regelfout, match=melding):
        indeling.bootsoort_toevoegen(naam, CLI)
    assert len(indeling.bootsoorten()) == 5 and not regels("bootsoort.toegevoegd")


def test_naam_van_50_tekens_mag(app):
    """De andere kant van de grens bij test_toevoegen_geweigerd[51-tekens]."""
    assert indeling.bootsoort_toevoegen("x" * 50, CLI).naam == "x" * 50


def test_database_vangt_gelijke_naam_als_regelfout(app, monkeypatch):
    """Een gelijktijdige gelijke naam komt langs de controle in het domein; de unieke index
    weigert hem en dat wordt een melding, geen 500."""
    monkeypatch.setattr(indeling, "_soortnaam", lambda naam, _id=None: naam)
    with pytest.raises(Regelfout, match="De bootsoort Kajak bestaat al"):
        indeling.bootsoort_toevoegen("Kajak", CLI)


# Criterium 3: hernoemen


def test_hernoemen_overal_nieuwe_naam_en_alles_blijft_gelijk(app):
    kajak = soort("Kajak")
    p = plaats(kajak.id)
    b = boten.boot_aanmaken("Zeemeeuw", kajak.id, lid().id, None, CLI)
    b2 = boten.boot_aanmaken("Fuut", kajak.id, lid("1002").id, None, CLI)
    wachtlijst.erop_zetten(b2.id, None, CLI)
    toewijzing.toewijzen(p.id, b.id, CLI)

    indeling.bootsoort_hernoemen(kajak.id, "Zeekajak", CLI)
    db.session.expire_all()

    assert p.boot_id == b.id and b.bootsoort_id == kajak.id
    assert [(k.naam, [w.boot.naam for w in rij]) for k, rij in wachtlijst.lijsten()] == [
        ("Zeekajak", ["Fuut"])]
    assert uitlezen.plaatsen()[0]["bootsoorten"] == ["Zeekajak"]
    assert {x["bootsoort"] for x in uitlezen.boten(False)} == {"Zeekajak"}
    assert uitlezen.wachtlijst(False)[0]["bootsoort"] == "Zeekajak"
    assert "Zeekajak" in boten.bootaantallen()[0]["aantallen"]
    [r] = regels("bootsoort.hernoemd")
    assert r.gegevens == {"naam": ["Kajak", "Zeekajak"]} and r.verwijzingen == [f"bootsoort:{kajak.id}"]


def test_export_toont_nieuwe_naam(app):
    kajak = soort("Kajak")
    plaats(kajak.id)
    indeling.bootsoort_hernoemen(kajak.id, "Zeekajak", CLI)
    blad = load_workbook(io.BytesIO(indeling.export("Botenloods"))).active
    assert blad["D2"].value == "(geschikt voor Zeekajak)"


def test_alleen_hoofdletters_wijzigen_mag_en_zonder_verschil_geen_logregel(app):
    kajak = soort("Kajak")
    indeling.bootsoort_hernoemen(kajak.id, " Kajak ", CLI)
    assert not regels("bootsoort.hernoemd")
    indeling.bootsoort_hernoemen(kajak.id, "KAJAK", CLI)
    assert soort("KAJAK").id == kajak.id


@pytest.mark.parametrize("naam, melding", [
    ("", "1 tot 50 tekens"),
    ("x" * 51, "1 tot 50 tekens"),
    ("surfSKI", "De bootsoort Surfski bestaat al"),
], ids=["leeg", "51-tekens", "naam-van-andere-soort"])
def test_hernoemen_geweigerd(app, naam, melding):
    kajak = soort("Kajak")
    with pytest.raises(Regelfout, match=melding):
        indeling.bootsoort_hernoemen(kajak.id, naam, CLI)
    db.session.expire_all()
    assert kajak.naam == "Kajak" and not regels("bootsoort.hernoemd")


def test_onbekende_soort(app):
    with pytest.raises(Regelfout, match="bestaat niet"):
        indeling.bootsoort_hernoemen(999, "Iets", CLI)
    with pytest.raises(Regelfout, match="bestaat niet"):
        indeling.bootsoort_verwijderen(999, CLI)


def test_twee_gelijktijdige_hernoemingen_loggen_de_juiste_oude_naam(app):
    """De eerste sessie hernoemt Kajak naar Zeekajak en commit pas later. De tweede moet wachten
    en dan Zeekajak als oude naam loggen. Zonder FOR UPDATE leest ze Kajak."""
    kajak = soort("Kajak")

    def tweede():
        indeling.bootsoorten()  # laad de soort eerst in de sessie (overlay §4)
        indeling.bootsoort_hernoemen(kajak.id, "Wildwaterkajak", CLI)

    fouten = race(app, ["SELECT id FROM bootsoort WHERE id = :s FOR UPDATE",
                        "UPDATE bootsoort SET naam = 'Zeekajak' WHERE id = :s"],
                  {"s": kajak.id}, tweede)
    assert not fouten
    [r] = regels("bootsoort.hernoemd")
    assert r.gegevens == {"naam": ["Zeekajak", "Wildwaterkajak"]}


# Criterium 2: verwijderen


def test_ongebruikte_soort_verwijderen(app):
    s = indeling.bootsoort_toevoegen("Waterfiets", CLI)
    indeling.bootsoort_verwijderen(s.id, CLI)
    assert db.session.get(Bootsoort, s.id) is None
    [r] = regels("bootsoort.verwijderd")
    assert r.gegevens == {"naam": "Waterfiets"} and r.verwijzingen == [f"bootsoort:{s.id}"]


@pytest.mark.parametrize("gebruik, melding", [
    ("boot", "in gebruik bij 1 boot\\."),
    ("plaats", "in gebruik bij 1 plaats\\."),
    ("beide", "in gebruik bij 2 boten en 1 plaats\\."),
])
def test_verwijderen_geweigerd_als_soort_in_gebruik(app, gebruik, melding):
    s = indeling.bootsoort_toevoegen("Waterfiets", CLI)
    if gebruik in ("boot", "beide"):
        boten.boot_aanmaken("Pedaalpiet", s.id, None, None, CLI)
    if gebruik == "beide":
        boten.boot_aanmaken("Trapper", s.id, None, None, CLI)
    if gebruik in ("plaats", "beide"):
        plaats(s.id)
    with pytest.raises(Regelfout, match=melding):
        indeling.bootsoort_verwijderen(s.id, CLI)
    db.session.expire_all()
    assert db.session.get(Bootsoort, s.id) is not None and not regels("bootsoort.verwijderd")


def test_verwijderen_wacht_op_een_nieuwe_boot_van_die_soort(app):
    """De eerste sessie maakt een boot van de soort en commit later. Verwijderen moet wachten en
    dan weigeren; zonder FOR UPDATE telt het 0 boten en geeft de FK een IntegrityError."""
    s = indeling.bootsoort_toevoegen("Waterfiets", CLI)
    fouten = race(app, ["INSERT INTO boot (naam, bootsoort_id) VALUES ('Pedaalpiet', :s)"],
                  {"s": s.id}, lambda: indeling.bootsoort_verwijderen(s.id, CLI))
    assert fouten == ["De bootsoort Waterfiets is in gebruik bij 1 boot. Wijzig of verwijder die eerst."]


@pytest.mark.parametrize("wat", ["boot", "plaats"])
def test_nieuwe_boot_of_plaats_wacht_op_een_lopende_verwijdering(app, wat):
    """De eerste sessie verwijdert de soort en commit later. Een nieuwe boot of plaats van die
    soort wacht en krijgt dan een melding; zonder KEY SHARE geeft de FK een IntegrityError."""
    s = indeling.bootsoort_toevoegen("Waterfiets", CLI)
    rek = indeling.rek_aanmaken("Rek A", CLI)
    actie = {"boot": lambda: boten.boot_aanmaken("Pedaalpiet", s.id, None, None, CLI),
             "plaats": lambda: indeling.plaats_aanmaken(rek.id, "A01", [s.id], False, CLI)}[wat]
    fouten = race(app, ["SELECT id FROM bootsoort WHERE id = :s FOR UPDATE",
                        "DELETE FROM bootsoort WHERE id = :s"], {"s": s.id}, actie)
    assert fouten == [{"boot": "Kies een bootsoort.",
                       "plaats": "Kies minstens één bootsoort die op de plaats past."}[wat]]


def test_boot_wijzigen_wacht_op_een_lopende_verwijdering(app):
    s = indeling.bootsoort_toevoegen("Waterfiets", CLI)
    b = boten.boot_aanmaken("Pedaalpiet", soort("Kajak").id, None, None, CLI)
    fouten = race(app, ["SELECT id FROM bootsoort WHERE id = :s FOR UPDATE",
                        "DELETE FROM bootsoort WHERE id = :s"], {"s": s.id},
                  lambda: boten.boot_wijzigen(b.id, "Pedaalpiet", s.id, None, CLI))
    assert fouten == ["Kies een bootsoort."]


def test_webrol_mag_bootsoorten_wijzigen(app, database):
    """botenloods_web heeft arwd op bootsoort; geen migratie nodig."""
    with database.connect() as c:
        rechten = c.execute(text(
            "SELECT privilege_type FROM information_schema.role_table_grants "
            "WHERE grantee = 'botenloods_web' AND table_name = 'bootsoort'")).scalars().all()
    assert {"SELECT", "INSERT", "UPDATE", "DELETE"} <= set(rechten)


# Scherm: blok Bootsoorten op /instellingen


def test_scherm_toevoegen_hernoemen_verwijderen(app, ingelogd):  # noqa: F811
    r = ingelogd.post("/bootsoorten", data={"naam": "Waterfiets"}, follow_redirects=True)
    assert "De bootsoort is toegevoegd." in r.text and 'value="Waterfiets"' in r.text
    s = soort("Waterfiets")
    r = ingelogd.post(f"/bootsoorten/{s.id}/naam", data={"naam": "Pedalo"}, follow_redirects=True)
    assert "De naam van de bootsoort is opgeslagen." in r.text and ">Pedalo<" in r.text
    assert "bootsoort.hernoemd" in ingelogd.get("/log/techniek").text
    assert "bootsoort.hernoemd" not in ingelogd.get("/log").text  # niet bij de bootmutaties
    boten.boot_aanmaken("Pedaalpiet", s.id, None, None, CLI)
    r = ingelogd.post(f"/bootsoorten/{s.id}/verwijderen", follow_redirects=True)
    assert "in gebruik bij 1 boot" in r.text
    assert "Pedalo" in ingelogd.get("/boten").text


@pytest.mark.parametrize("pad", ["/bootsoorten", "/bootsoorten/1/naam", "/bootsoorten/1/verwijderen"])
def test_scherm_vraagt_recente_inlog(app, ingelogd, pad):  # noqa: F811
    assert app.test_client().post(pad, data={"naam": "X"}).location.endswith("/inloggen")  # bezoeker
    with ingelogd.session_transaction() as sessie:
        sessie["ingelogd_op"] = int(time.time()) - 601
    r = ingelogd.post(pad, data={"naam": "Overgenomen"})
    assert r.status_code == 302 and r.location.endswith("/inloggen")
    db.session.expire_all()
    assert [x.naam for x in indeling.bootsoorten()] == [
        "Kajak", "Canadese kano", "Surfski", "C11", "Supboard"]
