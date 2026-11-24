"""Scherm Boten zonder plaats (#399): alle boten zonder plaats, met de knop Zet op de wachtlijst waar
wachtlijst.erop_zetten hem accepteert; een kijker leest mee zonder knop, status en leden (ADR-015)."""

import re
from datetime import timedelta

from app.domein import CLI, toewijzing, vandaag, wachtlijst
from tests.unit.hulp import lid, plaats
from tests.unit.test_indeling_en_toewijzing import boot
from tests.unit.test_kijkers import kijker, main  # noqa: F401 (fixture)
from tests.unit.test_overzichten_en_instellingen import opzeggen
from tests.unit.test_web_beheer import ingelogd  # noqa: F401 (fixture)

PAD = "/boten/zonder-plaats"


def vier_boten():
    """Een gewone boot, een clubboot, een boot van een oud-lid en een boot op de lijst, allemaal zonder plaats."""
    anna, bert, dirk = lid("1001", "Anna de Vries"), lid("1002", "Bert Fuut"), lid("2001", "Dirk Oud")
    gewoon, club, oud = boot(anna.id, naam="Gewoon"), boot(None, naam="Clubje"), boot(dirk.id, naam="Oudje")
    opzeggen(dirk.id, opzegdatum=vandaag() - timedelta(days=1))
    op_lijst = boot(bert.id, naam="Wachter")
    wachtlijst.erop_zetten(op_lijst.id, "2024-03-01", CLI)
    return gewoon, club, oud, op_lijst


def test_selectie_een_boot_met_plaats_valt_weg_en_de_rest_blijft(ingelogd):  # noqa: F811
    vier_boten()
    met_plaats = boot(lid("1003", "Cor Meeuw").id, naam="Geplaatst")
    toewijzing.toewijzen(plaats("A/1/1").id, met_plaats.id, CLI)
    tekst = main(ingelogd.get(PAD).text)
    assert "4 boten zonder plaats" in tekst and "Geplaatst" not in tekst
    assert all(naam in tekst for naam in ("Gewoon", "Clubje", "Oudje", "Wachter"))


def test_knop_alleen_waar_erop_zetten_hem_accepteert(ingelogd):  # noqa: F811
    gewoon, *_ = vier_boten()
    tekst = main(ingelogd.get(PAD).text)
    assert tekst.count('name="terug" value="zonder-plaats"') == 1
    assert f'action="/boten/{gewoon.id}/wachtlijst"' in tekst and "Zet Gewoon op de wachtlijst" in tekst
    assert tekst.count('<span data-label="Wachtlijst">kan niet op de wachtlijst</span>') == 2  # clubboot en oud-lid
    assert "op de wachtlijst sinds 01-03-2024" in tekst
    # Toets Design System: de oud-lid-tag achter de eigenaar, status en reden in de subregel, de actieregel alleen voor de knop.
    assert re.search(r'Dirk Oud</a> <span class="ds-tag">oud-lid</span> · <span data-label="Wachtlijst">kan niet', tekst)
    assert tekst.count('class="bl-item__actie"') == 1 and "Klik op de boot om een plaats toe te wijzen." in tekst


def test_de_knop_zet_de_boot_erop_met_vandaag_en_keert_terug(ingelogd):  # noqa: F811
    gewoon, *_ = vier_boten()
    r = ingelogd.post(f"/boten/{gewoon.id}/wachtlijst", data={"terug": "zonder-plaats"})
    assert r.location.endswith(PAD)
    tekst = ingelogd.get(PAD).text
    assert "De boot staat op de wachtlijst." in tekst and f"op de wachtlijst sinds {vandaag():%d-%m-%Y}" in tekst


def test_een_weigering_keert_ook_terug_naar_het_scherm(ingelogd):  # noqa: F811
    _, club, *_ = vier_boten()
    r = ingelogd.post(f"/boten/{club.id}/wachtlijst", data={"terug": "zonder-plaats"}, follow_redirects=True)
    assert "is een clubboot" in r.text and r.request.path == PAD


def test_zonder_terug_gaat_de_knop_naar_de_bootpagina(ingelogd):  # noqa: F811
    gewoon, *_ = vier_boten()
    assert ingelogd.post(f"/boten/{gewoon.id}/wachtlijst").location.endswith(f"/boten/{gewoon.id}")


def test_weigering_is_de_bron_van_erop_zetten(app):
    _, club, oud, _ = vier_boten()
    assert "clubboot" in wachtlijst.weigering(club) and "oud-lid" in wachtlijst.weigering(oud)
    assert wachtlijst.weigering(boot(lid("1009", "Eva").id, naam="Vrij")) is None


def test_lege_lijst_zegt_het(ingelogd):  # noqa: F811
    assert "Alle boten hebben een plaats." in ingelogd.get(PAD).text


def test_menu_item_staat_na_boten_zonder_eigenaar_zonder_telling_en_met_aria_current(ingelogd):  # noqa: F811
    vier_boten()
    tekst = ingelogd.get(PAD).text
    menu = re.search(r'<nav class="dj-menu__panel".*?</nav>', tekst, re.DOTALL).group(0)
    assert menu.index("Boten zonder eigenaar") < menu.index("Boten zonder plaats") < menu.index("Gaan opzeggen")
    assert 'href="/boten/zonder-plaats" aria-current="page">Boten zonder plaats</a>' in menu


def test_een_kijker_ziet_de_lijst_zonder_knop_status_en_leden(kijker):  # noqa: F811
    vier_boten()
    tekst = main(kijker.get(PAD).text)
    assert "Gewoon" in tekst and "Anna de Vries" in tekst and "Clubje" in tekst
    assert "<form" not in tekst and "wachtlijst" not in tekst.lower() and "/leden/" not in tekst
    assert "1001" not in tekst and 'href="/boten/' in tekst
    assert "oud-lid" not in tekst and "Klik op de boot" not in tekst and "bl-item__actie" not in tekst  # toets Design System


def test_een_kijker_krijgt_op_de_post_403_en_de_boot_blijft_af(kijker):  # noqa: F811
    gewoon, *_ = vier_boten()
    assert kijker.post(f"/boten/{gewoon.id}/wachtlijst", data={"terug": "zonder-plaats"}).status_code == 403
    assert gewoon.wachtlijst is None
