"""Boten zonder foto (issue #315, BV-88, BLB-049): de query, de volgorde, het scherm, de lege toestand en
het menu-item in Beheer."""

import re
from datetime import timedelta

import pytest
from sqlalchemy import create_engine, text

from app.domein import CLI, boten, indeling, toewijzing, vandaag
from app.models import Boot, db
from tests.unit.conftest import EIGENAAR
from tests.unit.hulp import lid, plaats, png
from tests.unit.test_blok1_schermen import menu_koppen, tekst_met_current
from tests.unit.test_web_beheer import ingelogd  # noqa: F401  fixture

PAD = "/boten-zonder-foto"


def zet(code, naam, lid_id=None, onbekend=False, foto=None, soort_id=1):
    """Een boot met die naam op die plaats (de plaats komt erbij als hij er nog niet is)."""
    b = boten.boot_aanmaken(naam, soort_id, lid_id, foto, CLI, clubboot=lid_id is None and not onbekend)
    if code:
        toewijzing.toewijzen(plaats(code).id, b.id, CLI)
    return b


def namen():
    return [b.naam for b in boten.zonder_foto()]


def regels(tekst):
    """De boten in de lijst, in de volgorde van het scherm."""
    return re.findall(r'data-label="Boot" href="/boten/\d+">([^<]+)</a>', tekst)


# Domein: wat erop staat


def test_een_boot_met_foto_staat_er_niet_op_en_een_boot_zonder_foto_wel(app):
    # Mutant: where(afbeelding_id.is_(None)) weglaten of omkeren valt hier (Met foto ontbreekt niet; Zonder foto wel).
    zet(None, "Zonder foto", onbekend=True)
    zet(None, "Met foto", onbekend=True, foto=png())
    assert namen() == ["Zonder foto"]


def test_een_boot_verdwijnt_uit_de_lijst_zodra_hij_een_foto_krijgt(app):
    b = zet("A/1/1", "Fuut")
    assert namen() == ["Fuut"]
    boten.foto_vervangen(b.id, png(), CLI)
    assert namen() == []


# Domein: volgorde


def test_volgorde_is_loodsvolgorde_dan_zonder_plaats_op_naam_en_id(app):
    # Namen staan tegen de plaatsvolgorde in, zodat een mutant die een sleutel weglaat een andere
    # lijst geeft. Mutants (verwachte lijst: Z1, Y1, X2, Aap, dan de boten zonder plaats):
    # - Rek.volgorde, Rek.id: zie de twee tests hieronder (de twee lopen in dit rek gelijk op);
    # - Plaats.verdieping weg: B/1/1, B/2/1, B/1/2 geeft Z1, X2, Y1;
    # - Plaats.vak weg: B/1/1 en B/1/2 vallen op naam, dus Y1 voor Z1;
    # - Boot.naam weg: de boten zonder plaats komen op id, dus Zeemeeuw voor Aap;
    # - Boot.id weg: zie test_gelijke_namen_staan_op_id.
    zet("B/1/1", "Z1")
    zet("B/1/2", "Y1")
    zet("B/2/1", "X2")
    zet("A/1/1", "Aap")
    zet(None, "Zeemeeuw", onbekend=True)
    zet(None, "Albatros", onbekend=True)
    assert namen() == ["Z1", "Y1", "X2", "Aap", "Albatros", "Zeemeeuw"]


def zet_volgorde(naam, volgorde):
    """Rek.volgorde wijzig je alleen als eigenaar; de applicatie kent geen scherm hiervoor."""
    engine = create_engine(EIGENAAR)
    with engine.begin() as verbinding:
        verbinding.execute(text("UPDATE rek SET volgorde = :v WHERE naam = :n"), {"v": volgorde, "n": naam})
    engine.dispose()


def test_volgorde_van_de_rekken_gaat_voor_hun_id(app):
    # Mutant: Rek.volgorde uit de sortering valt hier: rek A (id 2) heeft volgorde 0 en staat vooraan.
    zet("B/1/1", "Zwaluw")
    zet("A/1/1", "Aap")
    zet_volgorde("A", 0)
    db.session.expire_all()
    assert namen() == ["Aap", "Zwaluw"]


def test_bij_gelijke_volgorde_beslist_het_id_van_het_rek(app):
    # Mutant: Rek.id uit de sortering valt hier: dan staat A/1/1 (Aap) op naam voor B/1/1 (Zwaluw).
    zet("B/1/1", "Zwaluw")
    zet("A/1/1", "Aap")
    zet_volgorde("A", 5)
    zet_volgorde("B", 5)
    db.session.expire_all()
    assert namen() == ["Zwaluw", "Aap"]


def test_gelijke_namen_staan_op_id(app):
    # Mutant: Boot.id uit de sortering valt hier: het hoogste id staat eerst in de tabel en komt dan vooraan.
    db.session.add(Boot(id=900, naam="Dubbel", bootsoort_id=1))
    db.session.commit()
    db.session.add(Boot(id=800, naam="Dubbel", bootsoort_id=1))
    db.session.commit()
    assert [b.id for b in boten.zonder_foto()] == [800, 900]


# Scherm


def test_scherm_toont_kop_aantal_en_per_boot_naam_soort_eigenaar_en_plaats_met_links(ingelogd):  # noqa: F811
    anna = lid()
    b = zet("A/1/1", "Fuut", anna.id)
    zet(None, "Wulp", onbekend=True)
    tekst = ingelogd.get(PAD).text
    assert "<h1>Boten zonder foto</h1>" in tekst and '<p class="bl-aantal">2 boten zonder foto</p>' in tekst
    assert regels(tekst) == ["Fuut", "Wulp"]
    rij = tekst.split('<li class="bl-item">')[1]
    assert f'data-label="Boot" href="/boten/{b.id}">Fuut</a>' in rij
    assert '<span data-label="Bootsoort">Kajak</span>' in rij
    assert '<span data-label="Eigenaar">Anna de Vries</span>' in rij and "<a " not in rij.split('data-label="Eigenaar"')[1].split("</div>")[0]
    assert f'data-label="Plaats" href="/plaatsen/{b.plaats.id}">A/1/1</a>' in rij
    assert '<span data-label="Plaats">geen plaats</span>' in tekst.split('<li class="bl-item">')[2]


def test_aantal_in_enkelvoud_en_zonder_aantal_in_het_menu(ingelogd):  # noqa: F811
    # Mutant: 'boten' vast zetten valt op de eerste assert; een telling in het menu op de tweede (BV-88).
    zet("A/1/1", "Fuut")
    tekst = ingelogd.get(PAD).text
    assert '<p class="bl-aantal">1 boot zonder foto</p>' in tekst
    assert '>Boten zonder foto</a>' in tekst and "bl-nav__aantal" not in tekst


def test_eigenaar_is_lid_clubboot_of_onbekend_en_alleen_een_oud_lid_heeft_de_tag(ingelogd):  # noqa: F811
    # Mutant: de tag zonder is_oud_lid valt op Actief; `b.lid and` weglaten geeft een fout bij Club en Onbekend;
    # b.lid.naam vervangen door het lidnummer valt op de eerste assert.
    zet(None, "Actief", lid("1001", "Anna").id)
    zet(None, "Club")
    zet(None, "Onbekend", onbekend=True)
    oud = lid("1002", "Oud Lid", opzegdatum=vandaag() - timedelta(days=1))
    db.session.add(Boot(naam="Oudboot", bootsoort_id=1, lid_id=oud.id))  # boot() weigert een oud-lid
    db.session.commit()
    r = ingelogd.get(PAD)
    assert r.status_code == 200
    rij = {n: r.text.split(f">{n}</a>")[1].split("</li>")[0] for n in ("Actief", "Club", "Onbekend", "Oudboot")}
    assert '<span data-label="Eigenaar">Anna</span>' in rij["Actief"]
    assert '<span data-label="Eigenaar">clubboot</span>' in rij["Club"]
    assert '<span data-label="Eigenaar">eigenaar onbekend</span>' in rij["Onbekend"]
    assert '<span data-label="Eigenaar">Oud Lid</span> <span class="ds-tag">oud-lid</span>' in rij["Oudboot"]
    assert [n for n, x in rij.items() if "ds-tag" in x] == ["Oudboot"]


def test_scherm_escapet_boot_bootsoort_eigenaar_en_plaatscode(ingelogd):  # noqa: F811
    # Mutant: |safe op b.naam, b.bootsoort.naam, b.lid.naam of b.plaats.code valt hier.
    soort = indeling.bootsoort_toevoegen("<s>x", CLI)
    b = zet(None, "<b>x</b>", lid(naam="<i>Eva</i>").id, soort_id=soort.id)
    toewijzing.toewijzen(plaats("<u>x/1/1", (soort.id,)).id, b.id, CLI)
    tekst = ingelogd.get(PAD).text
    for ruw, veilig in (("<b>x</b>", "&lt;b&gt;x&lt;/b&gt;"), ("<i>Eva</i>", "&lt;i&gt;Eva&lt;/i&gt;"),
                        ("<s>x", "&lt;s&gt;x"), ("<u>x/1/1", "&lt;u&gt;x/1/1")):
        assert veilig in tekst and ruw not in tekst


def test_een_boot_met_foto_staat_niet_op_het_scherm(ingelogd):  # noqa: F811
    # Mutant: de query zonder filter valt hier.
    zet(None, "Met foto", onbekend=True, foto=png())
    tekst = ingelogd.get(PAD).text
    assert regels(tekst) == []


def test_zonder_boten_staat_er_de_lege_toestand(ingelogd):  # noqa: F811
    # Mutant: de melding weglaten of de lijst tonen zonder boten valt hier.
    zet(None, "Met foto", onbekend=True, foto=png())
    tekst = ingelogd.get(PAD).text
    assert re.search(r'<div class="ds-notice__body" role="status">Alle boten hebben een foto\.</div>', tekst)
    assert "bl-lijst" not in tekst and "bl-aantal" not in tekst


# Menu


def test_menu_heeft_het_item_als_laatste_in_boten_en_markeert_het_op_dit_scherm(ingelogd):  # noqa: F811
    # Mutant: een andere href of plek valt op de eerste assert; aria-current weglaten op de tweede.
    menu = ingelogd.get("/rekoverzicht").text
    assert menu_koppen(menu)[0]["Boten"][-1] == "Boten zonder foto" and 'href="/boten-zonder-foto"' in menu
    assert tekst_met_current(ingelogd, PAD) == ["Boten zonder foto"]
    assert tekst_met_current(ingelogd, "/boten") == ["Boten"]


def test_scherm_vraagt_inloggen(client):
    r = client.get(PAD)
    assert r.status_code == 302 and r.location.startswith("/inloggen")


@pytest.mark.parametrize("methode", ["post", "put", "delete"])
def test_scherm_kent_alleen_get(ingelogd, methode):  # noqa: F811
    assert getattr(ingelogd, methode)(PAD).status_code == 405
