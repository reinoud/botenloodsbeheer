"""De keuzerondjes op Gebruikers (Rol) en in de lidkeuze gebruiken `ds-radio` uit de basis, niet `dj-radio` (#345).
Mutant: een van beide sjablonen terug op `ds-check dj-radio`; beide asserts falen (Gebruikers: beheerders.html,
lidkeuze: _lidkeuze.html). De E2E-test staat in tests/e2e/test_lid_koppeling.py."""

import re

from tests.unit.hulp import lid
from tests.unit.test_gebruikers_rollen import scherm as _scherm
from tests.unit.test_gebruikers_rollen import twee as _twee
from tests.unit.test_lid_koppeling_web import pad

twee = _twee  # fixtures
scherm = _scherm


def rondjes(tekst):
    return re.findall(r'<div class="([^"]*)"><input type="radio"', tekst)


def test_rol_op_gebruikers_heeft_ds_radio(scherm):
    klassen = rondjes(scherm.get("/gebruikers").text)
    assert klassen == ["ds-check ds-radio"] * 2  # beheerder en kijker; mutant: dj-radio in beheerders.html


def test_lidkeuze_heeft_ds_radio(scherm, twee):
    lid("1001", "Sanne de Vries")
    klassen = rondjes(scherm.post(pad(twee[2]), data={"actie": "zoeken", "zoek": "vries"}).text)
    assert klassen == ["ds-check ds-radio"]  # de ene treffer; mutant: dj-radio in _lidkeuze.html
