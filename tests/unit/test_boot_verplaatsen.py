"""Boot verplaatsen (#206, ontwerp 5B): de oude plaats vrijgeven en de nieuwe toewijzen in één transactie, met
dezelfde controles als toewijzen. Een weigering laat de boot liggen en schrijft geen log (ADR-006)."""

import re

import pytest
from sqlalchemy import select

from app.domein import CLI, Regelfout, toewijzing, vandaag, wachtlijst
from app.models import Logregel, Plaats, Wachtlijst, db
from tests.unit.hulp import lid, race
from tests.unit.test_blok3b_detail import ingelogd, oud_lid_boot, taak  # noqa: F401 (fixture)
from tests.unit.test_indeling_en_toewijzing import acties, boot, plaats
from tests.unit.test_overzichten_en_instellingen import opzeggen


def liggen(code="A/1/1", naam="Zeemeeuw", lidnummer="1001"):
    """Een boot van een lid op de plaats met deze code."""
    p, b = plaats(code), boot(lid(lidnummer, f"Lid {lidnummer}").id, naam=naam)
    toewijzing.toewijzen(p.id, b.id, CLI)
    return p, b


def bezetter(p):
    return db.session.get(Plaats, p.id).boot_id


def blok(tekst):
    return re.search(r'<details class="dj-disclosure"[^>]*>\s*<summary id="verplaatsen-kop">.*?</details>', tekst, re.DOTALL).group(0)


# Domein


def test_verplaatsen_geeft_oude_plaats_vrij_en_wijst_nieuwe_toe_met_een_logregel(app):
    oud, b = liggen()
    nieuw = plaats("A/1/2")
    assert toewijzing.verplaatsen(b.id, nieuw.id, CLI) == "A/1/2"
    assert bezetter(oud) is None and bezetter(nieuw) == b.id
    assert acties()[-1] == "boot.verplaatst" and "plaats.vrijgegeven" not in acties()[3:]
    r = db.session.scalars(select(Logregel).order_by(Logregel.id.desc())).first()
    assert r.gegevens == {"van": "A/1/1", "naar": "A/1/2", "boot": "Zeemeeuw"}
    assert {f"plaats:{oud.id}", f"plaats:{nieuw.id}", f"boot:{b.id}", f"lid:{b.lid_id}"} <= set(r.verwijzingen)


def test_logregel_staat_onder_beide_plaatsen_en_de_boot(app):
    # Mutant: een van de beide plaatsverwijzingen weglaten valt op de eerste of de tweede assert.
    from app.domein import log
    oud, b = liggen()
    nieuw = plaats("A/1/2")
    toewijzing.verplaatsen(b.id, nieuw.id, CLI)
    for ref in (f"plaats:{oud.id}", f"plaats:{nieuw.id}", f"boot:{b.id}"):
        assert next(r.actie for r in log.regels([ref])) == "boot.verplaatst", ref


def test_wachtlijst_blijft_ongewijzigd(app):
    _oud, b = liggen()
    wacht = boot(lid("1002", "Bert Fuut").id, naam="Kievit")
    wachtlijst.erop_zetten(wacht.id, None, CLI)
    voor = db.session.execute(select(Wachtlijst.boot_id, Wachtlijst.aangemeld_op)).all()
    nieuw = plaats("A/1/2")
    aantal = len(acties())
    toewijzing.verplaatsen(b.id, nieuw.id, CLI)
    assert db.session.execute(select(Wachtlijst.boot_id, Wachtlijst.aangemeld_op)).all() == voor != []
    assert acties()[aantal:] == ["boot.verplaatst"]
    assert "wachtlijst.verwijderd" not in acties()


def test_bezette_plaats_geweigerd_boot_blijft_zonder_log(app):
    # Mutant: de bezet-controle weglaten overschrijft de andere boot en valt op de tweede assert.
    oud, b = liggen()
    anders = plaats("A/1/2")
    c = boot(lid("1002", "Bert Fuut").id, naam="Kievit")
    toewijzing.toewijzen(anders.id, c.id, CLI)
    voor = len(acties())
    with pytest.raises(Regelfout, match=r"^Plaats A/1/2 is niet meer vrij\. De boot blijft op A/1/1\.$"):
        toewijzing.verplaatsen(b.id, anders.id, CLI)
    assert bezetter(oud) == b.id and bezetter(anders) == c.id and len(acties()) == voor


def test_verkeerde_bootsoort_geweigerd_boot_blijft(app):
    # Mutant: controleer_past weglaten valt hier.
    oud, b = liggen()
    surf = plaats("A/1/2", soorten=("Surfski",))
    with pytest.raises(Regelfout, match=r"niet geschikt voor een kajak\. De boot blijft op A/1/1\."):
        toewijzing.verplaatsen(b.id, surf.id, CLI)
    assert bezetter(oud) == b.id and bezetter(surf) is None


def test_clubplaats_voor_boot_van_een_lid_geweigerd_en_clubboot_mag_naar_clubplaats(app):
    oud, b = liggen()
    club = plaats("A/1/2", club=True)
    with pytest.raises(Regelfout, match=r"is een clubplaats en alleen voor clubboten\. De boot blijft op A/1/1\."):
        toewijzing.verplaatsen(b.id, club.id, CLI)
    assert bezetter(oud) == b.id and bezetter(club) is None
    clubboot = boot(naam="Clubkajak")  # clubboot: mag naar een clubplaats
    gewoon = plaats("A/1/3")
    toewijzing.toewijzen(gewoon.id, clubboot.id, CLI)
    toewijzing.verplaatsen(clubboot.id, club.id, CLI)
    assert bezetter(club) == clubboot.id and bezetter(gewoon) is None


def test_oud_lid_boot_en_boot_zonder_plaats_en_dezelfde_plaats_en_onbekende_plaats_geweigerd(app):
    oud, b = liggen()
    nieuw = plaats("A/1/2")
    vrij = boot(lid("1002", "Bert Fuut").id, naam="Kievit")
    with pytest.raises(Regelfout, match="Kievit heeft geen plaats"):
        toewijzing.verplaatsen(vrij.id, nieuw.id, CLI)
    with pytest.raises(Regelfout, match=r"Zeemeeuw ligt al op plaats A/1/1"):
        toewijzing.verplaatsen(b.id, oud.id, CLI)
    with pytest.raises(Regelfout, match="Kies een bestaande plaats"):
        toewijzing.verplaatsen(b.id, nieuw.id + 99, CLI)
    with pytest.raises(Regelfout, match="Kies een vrije plaats"):
        toewijzing.verplaatsen(b.id, None, CLI)
    with pytest.raises(Regelfout, match="Deze boot bestaat niet"):
        toewijzing.verplaatsen(b.id + 99, nieuw.id, CLI)
    assert bezetter(oud) == b.id and bezetter(nieuw) is None
    assert "boot.verplaatst" not in acties()


def test_boot_van_oud_lid_wordt_niet_verplaatst(app):
    # Mutant: de oud-lidcontrole weglaten valt hier.
    p = plaats()
    anna = lid()
    b = boot(anna.id)
    toewijzing.toewijzen(p.id, b.id, CLI)
    opzeggen(anna.id, opzegdatum=vandaag())
    nieuw = plaats("A/1/2")
    with pytest.raises(Regelfout, match=r"is oud-lid\. De boot krijgt geen plaats\. De boot blijft op A/1/1"):
        toewijzing.verplaatsen(b.id, nieuw.id, CLI)
    assert bezetter(p) == b.id


# Gelijktijdig (ADR-003): de nieuwe plaats vergrendelen zodat één van twee slaagt

VERGRENDEL = "SELECT id FROM plaats WHERE id = :p FOR UPDATE"


def test_gelijktijdig_twee_boten_naar_dezelfde_plaats_een_slaagt(app):
    # Mutant: with_for_update weglaten uit de plaatsquery: de tweede sessie wacht niet (assert in race) of overschrijft.
    oud1, b1 = liggen("A/1/1", "Een")
    oud2 = plaats("A/1/2")
    b2 = boot(lid("1002", "Bert Fuut").id, naam="Twee")
    toewijzing.toewijzen(oud2.id, b2.id, CLI)
    doel = plaats("A/1/3")
    winnaar = boot(lid("1003", "Cor Wulp").id, naam="Drie")  # de eerste sessie legt deze boot op de doelplaats
    fouten = race(app, [VERGRENDEL, "UPDATE plaats SET boot_id = :b WHERE id = :p"], {"p": doel.id, "b": winnaar.id},
                  lambda: toewijzing.verplaatsen(b2.id, doel.id, CLI))
    assert fouten == ["Plaats A/1/3 is niet meer vrij. De boot blijft op A/1/2."]
    assert bezetter(doel) == winnaar.id and bezetter(oud2) == b2.id and bezetter(oud1) == b1.id


def test_gelijktijdig_oude_plaats_intussen_vrijgegeven(app):
    # Mutant: populate_existing weglaten of de controle oud.boot_id != b.id: de verplaatsing slaagt op een lege plaats.
    oud, b = liggen()
    nieuw = plaats("A/1/2")
    fouten = race(app, [VERGRENDEL, "UPDATE plaats SET boot_id = NULL WHERE id = :p"], {"p": oud.id},
                  lambda: toewijzing.verplaatsen(b.id, nieuw.id, CLI))
    assert fouten == ["Boot Zeemeeuw heeft geen plaats."]
    assert bezetter(nieuw) is None and bezetter(oud) is None


# Web


def test_post_verplaatst_en_toont_melding_en_de_boot_staat_op_de_nieuwe_plaats(ingelogd):  # noqa: F811
    oud, b = liggen()
    nieuw = plaats("A/1/2")
    r = ingelogd.post(f"/boten/{b.id}/verplaatsen", data={"plaats_id": nieuw.id})
    assert r.status_code == 302 and r.headers["Location"] == f"/boten/{b.id}"
    tekst = ingelogd.get(r.headers["Location"]).text
    assert "De boot is verplaatst." in tekst
    assert '<h2 class="bl-taak__kop" id="taak-kop">Op plaats A/1/2</h2>' in taak(tekst)
    assert bezetter(nieuw) == b.id and bezetter(oud) is None


@pytest.mark.parametrize("waarde", [None, "", "abc", "9999999"])
def test_post_weigert_en_opent_het_blok(ingelogd, waarde):  # noqa: F811
    # Mutant: open=verplaatsen weglaten in de redirect valt op de Location-assert.
    oud, b = liggen()
    r = ingelogd.post(f"/boten/{b.id}/verplaatsen", data={} if waarde is None else {"plaats_id": waarde})
    assert r.status_code == 302 and r.headers["Location"] == f"/boten/{b.id}?open=verplaatsen"
    tekst = ingelogd.get(r.headers["Location"]).text
    assert re.search(r'<details class="dj-disclosure" open>\s*<summary id="verplaatsen-kop">', tekst)
    assert bezetter(oud) == b.id


def test_post_op_bezette_plaats_toont_de_zin_uit_het_ontwerp(ingelogd):  # noqa: F811
    _oud, b = liggen()
    anders = plaats("A/1/2")
    toewijzing.toewijzen(anders.id, boot(lid("1002", "Bert Fuut").id, naam="Kievit").id, CLI)
    r = ingelogd.post(f"/boten/{b.id}/verplaatsen", data={"plaats_id": anders.id}, follow_redirects=True)
    assert "Plaats A/1/2 is niet meer vrij. De boot blijft op A/1/1." in r.text


def test_post_onbekende_boot_is_404(ingelogd):  # noqa: F811
    assert ingelogd.post("/boten/9999/verplaatsen", data={"plaats_id": 1}).status_code == 404


def test_post_zonder_inloggen_verplaatst_niets(client):
    oud, b = liggen()
    nieuw = plaats("A/1/2")
    r = client.post(f"/boten/{b.id}/verplaatsen", data={"plaats_id": nieuw.id})
    assert r.status_code in (302, 400, 401, 403) and bezetter(oud) == b.id


def test_blok_dicht_met_lege_keuze_en_alleen_vrije_plaatsen_voor_de_soort(ingelogd):  # noqa: F811
    # Mutant: de bootsoort uit vrije_plaatsen halen toont ook de surfskiplaats; open weglaten valt op de eerste assert.
    _oud, b = liggen()
    vrij = plaats("A/1/2")
    plaats("A/1/3", soorten=("Surfski",))
    bezet = plaats("A/1/4")
    toewijzing.toewijzen(bezet.id, boot(lid("1002", "Bert Fuut").id, naam="Kievit").id, CLI)
    t = blok(ingelogd.get(f"/boten/{b.id}").text)
    assert "<details class=\"dj-disclosure\">" in t and " open" not in t.split(">")[0]
    assert '<option value="">Kies een vrije plaats</option>' in t
    assert re.findall(r'<option value="(\d+)"', t) == [str(vrij.id)]
    assert 'Verplaats naar een vrije plaats voor kajak' in t and '>Verplaats</button>' in t
    assert 'required' in t


def test_geen_vrije_plaats_geeft_de_zin_en_geen_knop(ingelogd):  # noqa: F811
    _oud, b = liggen()
    plaats("A/1/2", soorten=("Surfski",))
    t = blok(ingelogd.get(f"/boten/{b.id}").text)
    assert "<p>Er is geen vrije plaats voor kajak.</p>" in t and "<button" not in t and "<select" not in t


def test_blok_ontbreekt_zonder_plaats_en_bij_oud_lid_en_staat_tussen_taak_en_wijzigen(ingelogd):  # noqa: F811
    plaats()
    zonder = boot(lid("1005", "Eva Smit").id)
    assert "verplaatsen-kop" not in ingelogd.get(f"/boten/{zonder.id}").text
    assert "verplaatsen-kop" not in ingelogd.get(f"/boten/{oud_lid_boot().id}").text
    _oud, b = liggen("A/1/2", "Fuut")
    t = ingelogd.get(f"/boten/{b.id}").text
    assert t.index('id="taak-kop"') < t.index('id="verplaatsen-kop"') < t.index('id="wijzigen-kop"')


def test_clubboot_ziet_clubplaatsen_en_gewone_plaatsen_apart(ingelogd):  # noqa: F811
    gewoon = plaats("A/1/1")
    club = plaats("A/1/2", club=True)
    vrij = plaats("A/1/3")
    b = boot(naam="Clubkajak")
    toewijzing.toewijzen(gewoon.id, b.id, CLI)
    t = blok(ingelogd.get(f"/boten/{b.id}").text)
    assert t.index('<optgroup label="Clubplaatsen">') < t.index(f'value="{club.id}"') < t.index('<optgroup label="Gewone plaatsen">') < t.index(f'value="{vrij.id}"')


def test_boot_verplaatst_staat_in_het_bootlog_en_op_de_overzichten(ingelogd):  # noqa: F811
    # Mutant: boot verplaatst uit acties=("plaats.", ...) van /vrij halen valt op de tweede assert.
    oud, b = liggen()
    nieuw = plaats("A/1/2")
    ingelogd.post(f"/boten/{b.id}/verplaatsen", data={"plaats_id": nieuw.id})
    for pad in ("/log", f"/boten/{b.id}", f"/plaatsen/{oud.id}", f"/plaatsen/{nieuw.id}", "/vrij", "/boten"):
        assert "boot verplaatst" in ingelogd.get(pad).text, pad
    assert re.search(r"van: A/1/1; \w+: Zeemeeuw; naar: A/1/2|van: A/1/1; naar: A/1/2", ingelogd.get("/log").text)
