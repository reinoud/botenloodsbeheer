"""Export en import van de rekindeling als CSV (issue #157, ADR-014 §1 en §2). Een regel per
plaats: rek;omschrijving;verdieping;vak;bootsoorten;clubplaats. De import vult aan en werkt bij,
alles of niets, en laat plaatsen buiten het bestand staan."""

import re
from dataclasses import dataclass

from sqlalchemy import func, select

from app.domein import Regelfout, csvbestand, indeling, log
from app.domein.csvbestand import CsvFout
from app.models import Bootsoort, Plaats, Rek, db

KOLOMMEN = ("rek", "omschrijving", "verdieping", "vak", "bootsoorten", "clubplaats")
_GETAL = re.compile(r"\d{1,2}", re.ASCII)

UITLEG = (
    "# Rekindeling van de botenloods. Regels die met # beginnen zijn commentaar en worden genegeerd.",
    "# Een regel per plaats. Gebruik een puntkomma als scheidingsteken en sla het bestand op als CSV UTF-8.",
    f"# rek: de naam van het rek, hooguit {indeling.NAAM_MAX} tekens, zonder / en zonder # vooraan.",
    f"# omschrijving: hooguit {indeling.OMSCHRIJVING_MAX} tekens, gelijk op alle regels van hetzelfde rek.",
    (f"# verdieping: {indeling.VERDIEPINGEN[0]} tot en met {indeling.VERDIEPINGEN[-1]}. "
     f"vak: {indeling.VAKKEN[0]} tot en met {indeling.VAKKEN[-1]}. Een verdieping loopt van vak 1 "
     "zonder gaten."),
    ("# bootsoorten: de bootsoorten die op de plaats passen, gescheiden door /. Leeg betekent geen "
     "bootsoort, en kan alleen bij een nieuwe plaats of een plaats die al geen bootsoort heeft."),
    "# clubplaats: ja of nee.",
    ("# Importeren vult aan en werkt bij: een nieuw rek of een nieuwe plaats komt erbij, een "
     "bestaande plaats krijgt de waarden uit het bestand."),
    ("# Plaatsen die niet in het bestand staan, blijven zoals ze zijn. Op een plaats met een boot "
     "moet de bootsoort van die boot blijven staan."),
    "# Is er een fout in een regel, dan wordt niets geïmporteerd.",
)


def export(leeg=False):
    """De indeling als CSV; leeg=True geeft het sjabloon met uitleg en een voorbeeldregel."""
    soorten = indeling.bootsoorten()
    for s in soorten:
        if "/" in s.naam:
            raise Regelfout(f"De bootsoort {s.naam} bevat een /. Hernoem die eerst bij de "
                            "instellingen, want de export scheidt bootsoorten met een /.")
    if leeg:
        voorbeeld = "/".join(s.naam for s in soorten[:2]) or "Kajak"
        rijen = [[t] for t in UITLEG]
        rijen.append(["# Bootsoorten in deze installatie: " + ", ".join(s.naam for s in soorten)])
        rijen.append(["# Voorbeeld: A", "Stelling links", 1, 1, voorbeeld, "nee"])
        rijen.append(KOLOMMEN)
        return csvbestand.schrijf(rijen)
    rijen = [KOLOMMEN]
    for r in indeling.rekken():
        if r.naam.startswith("#"):
            raise Regelfout(f"De naam van rek {r.naam} begint met #. Hernoem het rek eerst, want "
                            "een regel met # vooraan is commentaar.")
        rijen += [(r.naam, r.omschrijving, p.verdieping, p.vak,
                   "/".join(s.naam for s in p.bootsoorten), "ja" if p.is_clubplaats else "nee")
                  for p in r.plaatsen]
    return csvbestand.schrijf(rijen)


@dataclass
class _Regel:
    regel: int
    rek: str
    omschrijving: str
    paar: tuple
    soortnamen: list
    clubplaats: bool


def _kort(tekst):
    return tekst if len(tekst) <= 30 else tekst[:30] + "…"


def _op_regel(meldingen):
    return sorted(meldingen, key=lambda m: int(m.split(":")[0].split()[1]))


def _lees_regels(rijen, meldingen):
    """De velden van elke regel gecontroleerd, zonder de database. Fouten komen in meldingen."""
    regels, per_plaats, omschrijvingen = [], {}, {}
    for nr, cel in rijen:
        aantal = len(meldingen)

        def fout(tekst, nr=nr):
            meldingen.append(f"Regel {nr}: {tekst}")

        def veld(functie, kolom, fout=fout, cel=cel):
            try:
                return functie(cel[kolom])
            except Regelfout as f:
                fout(str(f))

        rek, omschrijving = veld(indeling._naam, "rek"), veld(indeling._omschrijving, "omschrijving")
        paar = []
        for kolom, bereik in (("verdieping", indeling.VERDIEPINGEN), ("vak", indeling.VAKKEN)):
            if _GETAL.fullmatch(cel[kolom]) and int(cel[kolom]) in bereik:
                paar.append(int(cel[kolom]))
            else:
                fout(f"{kolom} moet een getal van {bereik[0]} tot en met {bereik[-1]} zijn.")
        # Een lege cel is een plaats zonder bootsoort; wanneer dat mag, zie _controleer.
        soortnamen = list(dict.fromkeys(s.strip() for s in cel["bootsoorten"].split("/"))) \
            if cel["bootsoorten"] else []
        if "" in soortnamen:
            fout("bootsoorten mist een naam: gebruik namen gescheiden door één /, zonder lege plek.")
        if cel["clubplaats"].lower() not in ("ja", "nee"):
            fout("clubplaats moet ja of nee zijn.")
        if len(meldingen) > aantal:
            continue
        sleutel = (rek.lower(), tuple(paar))
        if sleutel in per_plaats:
            fout(f"plaats {rek}/{paar[0]}/{paar[1]} staat al op regel {per_plaats[sleutel]}.")
            continue
        per_plaats[sleutel] = nr
        eerste = omschrijvingen.setdefault(rek.lower(), (nr, omschrijving))
        if eerste[1] != omschrijving:
            fout(f"de omschrijving van rek {rek} wijkt af van regel {eerste[0]}.")
            continue
        regels.append(_Regel(nr, rek, omschrijving, tuple(paar), soortnamen,
                             cel["clubplaats"].lower() == "ja"))
    return regels


def importeren(data, actor):
    """Verwerkt het bestand in één transactie. Bij één fout verandert er niets en meldt CsvFout
    elke foute regel. Geeft de aantallen {rekken_nieuw, rekken_gewijzigd, plaatsen_nieuw,
    plaatsen_gewijzigd}; alleen die aantallen komen in het technische log."""
    rijen, meldingen = csvbestand.lees(data, KOLOMMEN)
    regels = _lees_regels(rijen, meldingen)
    if meldingen:
        raise CsvFout(_op_regel(meldingen))
    aantallen = dict.fromkeys(("rekken_nieuw", "rekken_gewijzigd", "plaatsen_nieuw",
                               "plaatsen_gewijzigd"), 0)
    if not regels:
        return aantallen
    try:
        _verwerk(regels, actor, aantallen)
        if any(aantallen.values()):
            log.schrijf(actor, "indeling.geimporteerd", [], aantallen)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return aantallen


def _vergrendel(namen):
    """Eerst de bestaande rekken, dan hun plaatsen, dan de bootsoorten met KEY SHARE, in vaste
    volgorde zoals indeling_instellen en _soorten (ADR-014 §2)."""
    rekken = db.session.scalars(
        select(Rek).where(func.lower(Rek.naam).in_(namen)).order_by(Rek.id).with_for_update()
        .execution_options(populate_existing=True)).all()
    plaatsen = db.session.scalars(
        select(Plaats).where(Plaats.rek_id.in_([r.id for r in rekken])).order_by(Plaats.id)
        .with_for_update(of=Plaats).execution_options(populate_existing=True)).all()
    soorten = db.session.scalars(
        select(Bootsoort).order_by(Bootsoort.id).with_for_update(key_share=True)).all()
    return {r.naam.lower(): r for r in rekken}, plaatsen, soorten


def _controleer(groepen, bestaand, plaatsen, soorten):
    """Wat de database erbij zegt: bootsoorten, gaten in een verdieping, een bezette plaats.
    Geeft per regel de gekozen Bootsoorten, en weigert met alle meldingen tegelijk."""
    exact = {s.naam: s for s in soorten}
    zonder_hoofdletters = {}
    for s in soorten:
        zonder_hoofdletters.setdefault(s.naam.lower(), []).append(s)
    huidig = {(p.rek_id, p.verdieping, p.vak): p for p in plaatsen}
    meldingen, gekozen = [], {}
    for groep in groepen.values():
        for r in groep:
            gevonden = []
            for n in r.soortnamen:
                kandidaten = [exact[n]] if n in exact else zonder_hoofdletters.get(n.lower(), [])
                if len(kandidaten) == 1:
                    gevonden.append(kandidaten[0])
                else:
                    meldingen.append(f"Regel {r.regel}: de bootsoort {_kort(n)} "
                                     + ("bestaat niet." if not kandidaten else
                                        "is dubbelzinnig, schrijf hem precies zoals in de applicatie."))
            if len(gevonden) == len(r.soortnamen):
                gekozen[r.regel] = sorted(set(gevonden), key=lambda s: s.id)
    for naam, groep in groepen.items():
        rek = bestaand.get(naam)
        try:
            indeling._vakken({r.paar for r in groep} | _paren(rek, plaatsen))
        except Regelfout as f:
            meldingen.append(f"Regel {groep[0].regel}: rek {groep[0].rek}: {f}")
        for r in groep:
            p = huidig.get((rek.id, *r.paar)) if rek else None
            if p is not None and r.regel in gekozen:
                try:
                    if not gekozen[r.regel] and p.bootsoorten:  # zoals plaats_wijzigen (_soorten)
                        raise Regelfout(indeling.GEEN_SOORT)
                    indeling.controleer_plaats(p, gekozen[r.regel], r.clubplaats)
                except Regelfout as f:
                    meldingen.append(f"Regel {r.regel}: {f}")
    if meldingen:
        raise CsvFout(_op_regel(meldingen))
    return gekozen


def _paren(rek, plaatsen):
    return {(p.verdieping, p.vak) for p in plaatsen if rek and p.rek_id == rek.id}


def _verwerk(regels, actor, aantallen):
    groepen = {}
    for r in regels:
        groepen.setdefault(r.rek.lower(), []).append(r)
    bestaand, plaatsen, soorten = _vergrendel(set(groepen))
    gekozen = _controleer(groepen, bestaand, plaatsen, soorten)

    nieuw, reks = set(), {}
    for naam, groep in groepen.items():
        rek = bestaand.get(naam)
        if rek is None:
            rek = indeling._rek_aanmaken(groep[0].rek, groep[0].omschrijving,
                                         {r.paar for r in groep}, actor)
            aantallen["rekken_nieuw"] += 1
            erbij = {r.paar for r in groep}
        else:
            if rek.omschrijving != groep[0].omschrijving:
                indeling._rek_wijzigen(rek, rek.naam, groep[0].omschrijving, actor)
                aantallen["rekken_gewijzigd"] += 1
            erbij = {r.paar for r in groep} - _paren(rek, plaatsen)
            if erbij:
                indeling._plaatsen_erbij(rek, erbij, actor, {})
        nieuw |= {(rek.id, *paar) for paar in erbij}
        reks[naam] = rek
    aantallen["plaatsen_nieuw"] = len(nieuw)
    alle = {(p.rek_id, p.verdieping, p.vak): p for p in db.session.scalars(
        select(Plaats).where(Plaats.rek_id.in_([r.id for r in reks.values()])))}
    for naam, groep in groepen.items():
        for r in groep:
            sleutel = (reks[naam].id, *r.paar)
            if indeling._plaats_wijzigen(alle[sleutel], gekozen[r.regel], r.clubplaats, actor) \
                    and sleutel not in nieuw:
                aantallen["plaatsen_gewijzigd"] += 1
