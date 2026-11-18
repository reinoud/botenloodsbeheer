"""Een lid kiezen met zoeken en een tussenstap (BV-85, #295). Het zoekveld en de treffers (keuzerondjes
met het lidnummer als waarde) horen bij elk scherm waar een beheerder een lid kiest: de bezettingsimport,
Nieuwe boot en Boot wijzigen.

De zoekterm en de gekozen waarde komen uit het formulier en zijn externe invoer. De server herkent een
keuze alleen als de waarde het lidnummer is van een lid dat `kiesbare_leden` levert, of `clubboot`.
Niets hier logt een term."""

import re
from dataclasses import dataclass, field

from app.domein import leden
from app.domein.zoekopdracht import MIN_TEKENS, schoon

MAX_TREFFERS = 10
# "Naam (lidnummer)" kan 100 + 2 + 20 + 1 tekens zijn (Lid.naam, Lid.lidnummer): een kortere grens kapt
# het lidnummer af, en dan herkent veld() de tekst niet meer als de keuze van een bestaande boot (#316).
MAX_TEKENS = 123
CLUBBOOT = "clubboot"  # de term die de clubboot als treffer geeft, en de waarde van zijn rondje
TE_KORT = f"Geef minstens {MIN_TEKENS} tekens op. Zoek op een deel van de naam of op het lidnummer."
GEEN_LID = "Geen lid gevonden. Zoek op een deel van de naam of op het lidnummer."
NIET_GEKOZEN = "Kies een lid uit de treffers. Zoek eerst met de knop Zoeken."
ONGELDIG = "Dit lid kan niet worden gekozen. Zoek opnieuw."
KEUZES_ONGELDIG = "De keuzes kloppen niet meer. Ververs de pagina en probeer het opnieuw."
EIGENAAR_LEEG = ("Vul een eigenaar in. Een boot van een lid of oud-lid kan niet zonder eigenaar. "
                 "Zoek op naam of lidnummer.")
# Het veld Eigenaar van een bestaande boot is gevuld met "Naam (lidnummer)": zoeken daarop zoekt het nummer.
_LABEL = re.compile(r".+ \(([^()]+)\)")


@dataclass
class Treffer:
    waarde: str  # het lidnummer, of CLUBBOOT
    lid: object = None  # het Lid; None voor de clubboot

    @property
    def oud(self):
        """Een oud-lid krijgt de ds-tag "oud-lid" achter het label (BV-86)."""
        return self.lid is not None and leden.is_oud_lid(self.lid)


@dataclass
class Keuzeveld:
    """De toestand van één zoekveld voor het sjabloon."""

    term: str = ""
    treffers: list = field(default_factory=list)  # hooguit MAX_TREFFERS
    meer: bool = False  # er zijn meer treffers dan getoond
    gekozen: str = ""  # de waarde van het aangevinkte rondje
    fout: str = ""


def kiesbare_leden(zoek="", oud=False):
    """De leden die een keuze mag opleveren, eventueel gefilterd op naam of lidnummer. Dit is de enige
    plek die bepaalt wie kiesbaar is: de actieve leden, en met oud=True ook de oud-leden binnen de
    bewaartermijn (#298). De bezettingsimport vraagt altijd oud=False."""
    return leden.actieve_leden(zoek, met_oud=oud)


def lid_van_waarde(waarde, oud=False):
    """Het kiesbare lid met dit lidnummer, of None (onbekend, of een oud-lid waar dat niet mag)."""
    return next((lid for lid in kiesbare_leden("", oud) if lid.lidnummer == waarde), None)


def veld(term, keuze="", club=True, oud=False):
    """Zoekt na de knop Zoeken. `keuze` is het rondje dat het formulier meestuurde: het blijft alleen
    gekozen als het nog een treffer is. Precies één treffer staat al gekozen. Te kort of zonder treffer
    geeft een foutregel."""
    term = schoon(term, MAX_TEKENS)
    if len(term) < MIN_TEKENS:
        return Keuzeveld(term, fout=TE_KORT)
    zoek = m.group(1) if (m := _LABEL.fullmatch(term)) else term
    treffers = [Treffer(CLUBBOOT)] if club and zoek.casefold() == CLUBBOOT else []
    treffers += [Treffer(lid.lidnummer, lid) for lid in kiesbare_leden(zoek, oud)]
    if not treffers:
        return Keuzeveld(term, fout=GEEN_LID)
    alle = [t.waarde for t in treffers]
    if keuze in alle[MAX_TREFFERS:]:  # een gekozen rondje valt niet weg achter de tiende treffer
        treffers.insert(0, treffers.pop(alle.index(keuze)))
    getoond = treffers[:MAX_TREFFERS]
    waarden = [t.waarde for t in getoond]
    gekozen = keuze if keuze in waarden else waarden[0] if len(waarden) == 1 else ""
    return Keuzeveld(term, getoond, len(treffers) > MAX_TREFFERS, gekozen)


def veld_gekozen(term, lid):
    """Het veld van een keuze die al vaststaat (een eerder opgeslagen keuze): één rondje, gekozen.
    lid None is de clubboot."""
    treffer = Treffer(lid.lidnummer, lid) if lid else Treffer(CLUBBOOT)
    return Keuzeveld(term, [treffer], gekozen=treffer.waarde)


def eigenaar(keuze, term, boot=None, boot_tekst=""):
    """Wat een formulier met één keuze (Nieuwe boot, Boot wijzigen) betekent:
    ((lid_id, clubboot), None), of (None, Keuzeveld met een foutregel). `keuze` is het aangevinkte
    rondje, `term` het zoekveld. Zonder rondje geldt: het ongewijzigde zoekveld van een bestaande boot
    (`boot_tekst`) laat de eigenaar staan; een andere term is geen keuze; een leeg veld is eigenaar
    onbekend, behalve bij een boot van een lid of oud-lid (#295, 4A). Een clubboot
    mag onbekend worden (#233)."""
    keuze, term = (keuze or "").strip(), schoon(term, MAX_TEKENS)
    if keuze == CLUBBOOT:
        return (None, True), None
    if keuze:
        lid = lid_van_waarde(keuze, oud=True)
        return ((lid.id, False), None) if lid else (None, Keuzeveld(term, fout=ONGELDIG))
    if term:
        if boot is not None and term == boot_tekst:
            return (boot.lid_id, boot.clubboot), None
        return None, Keuzeveld(term, fout=NIET_GEKOZEN)
    if boot is not None and boot.lid_id is not None:
        return None, Keuzeveld(fout=EIGENAAR_LEEG)
    return (None, False), None
