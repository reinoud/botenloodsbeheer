"""Export en import van de bezetting als CSV (issue #158, ADR-014 §1, §3 en §4). Een regel per bezette
plaats: plaats;boot;bootsoort;eigenaar;lidnummer. Na de upload staat het bestand als lopende import
in de database (hooguit één voor de installatie); de beheerder koppelt namen aan leden en
bevestigt, en dan voert één transactie alles uit of niets. Het bestand is externe invoer: geen
naam of veld eruit komt in het technische log of in een melding die in de cookie belandt."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.domein import Regelfout, boten, csvbestand, indeling, leden, log, toewijzing
from app.domein.csvbestand import CsvFout
from app.models import Bezettingsimport, Boot, Bootsoort, Lid, Naamkoppeling, Plaats, Rek, db

KOLOMMEN = ("plaats", "boot", "bootsoort", "eigenaar", "lidnummer")
VERLOOP = timedelta(hours=2)
BOOT_MAX = 100  # lengte van Boot.naam
EIGENAAR_MAX = 100  # lengte van Lid.naam en Naamkoppeling.naam
CLUBBOOT = "clubboot"  # in de kolom eigenaar; leeg is een onbekende eigenaar (#204)
_GETAL = re.compile(r"\d{1,2}", re.ASCII)

OVERGESLAGEN, TE_KOPPELEN, FOUT = "overgeslagen", "te koppelen", "fout"
SOORT = "soort-"  # voorvoegsel in imp.keuzes voor de gekozen bootsoort van een regel (#202)
EIGENAAR_ONGEKOPPELD = "Geen lid gevonden, of meer dan één. Kies een lid of de vereniging."
GEEN_ACTIE = ("ongewijzigd", OVERGESLAGEN)
BLOKKEERT = (TE_KOPPELEN, FOUT)

UITLEG = (
    "# Bezetting van de botenloods. Regels die met # beginnen zijn commentaar en worden genegeerd.",
    "# Een regel per bezette plaats. Gebruik een puntkomma als scheidingsteken en sla het bestand op als CSV UTF-8.",
    "# plaats: de aanduiding van de plaats, rek/verdieping/vak, bijvoorbeeld A/1/1.",
    (f"# boot: de naam van de boot, hooguit {BOOT_MAX} tekens. bootsoort: een bootsoort zoals de "
     "applicatie hem toont."),
    ("# eigenaar en lidnummer: het lid dat de boot bezit. Het lidnummer gaat voor, zonder lidnummer "
     "zoekt de import het lid op exacte naam. Voor een clubboot schrijf je clubboot bij eigenaar en laat je "
     "het lidnummer leeg. Zijn beide leeg, dan is de eigenaar onbekend: de boot komt op de pagina Boten "
     "zonder eigenaar en op een gewone plaats."),
    ("# Een naam die niet bij precies één lid past, koppel je na het uploaden in een scherm aan een "
     "lid of aan de vereniging. Die keuze wordt onthouden voor een volgende import."),
    ("# Een boot die nog niet bestaat, wordt aangemaakt. Ligt er al een andere boot op de plaats, "
     "dan gaat die van de plaats en blijft bestaan. Een boot die elders ligt, wordt verplaatst."),
    "# Na het uploaden zie je eerst een overzicht. Er verandert niets tot je bevestigt.",
)


def _kort(tekst):
    return tekst if len(tekst) <= 30 else tekst[:30] + "…"


def export(leeg=False):
    """De bezetting als CSV; leeg=True geeft het sjabloon met uitleg en voorbeeldregels."""
    if leeg:
        soorten = indeling.bootsoorten()
        voorbeeld = soorten[0].naam if soorten else "Kajak"
        rijen = [[t] for t in UITLEG]
        rijen.append(["# Bootsoorten in deze installatie: " + ", ".join(s.naam for s in soorten)])
        rijen.append(["# Voorbeeld: A/1/1", "Zeemeeuw", voorbeeld, "Anna de Vries", "1001"])
        rijen.append(["# Voorbeeld clubboot: B/1/1", "Clubkajak", voorbeeld, CLUBBOOT, ""])
        rijen.append(KOLOMMEN)
        return csvbestand.schrijf(rijen)
    rijen = [KOLOMMEN]
    for r in indeling.rekken():
        if r.naam.startswith("#"):
            raise Regelfout(f"De naam van rek {r.naam} begint met #. Hernoem het rek eerst, want "
                            "een regel met # vooraan is commentaar.")
        for p in r.plaatsen:
            b = p.boot
            if b is not None:
                rijen.append((p.code, b.naam, b.bootsoort.naam,
                              b.lid.naam if b.lid else CLUBBOOT if b.clubboot else "",
                              b.lid.lidnummer if b.lid else ""))
    if any(indeling._stuurteken(str(cel)) for rij in rijen for cel in rij):
        raise Regelfout("Een naam van een boot of eigenaar bevat een stuurteken of regeleinde. "
                        "Pas die eerst aan, want een CSV-bestand kan dat niet bevatten.")
    return csvbestand.schrijf(rijen)


# Lopende import


def verlopen_opruimen():
    """Verwijdert verlopen imports; web doet dit bij elke upload en elk koppelscherm, de
    dagelijkse opschoning ook (ADR-014 §3)."""
    aantal = db.session.execute(delete(Bezettingsimport).where(
        Bezettingsimport.verloopt_op <= func.now())).rowcount
    db.session.commit()
    return aantal


def lopend(vergrendel=False):
    """De lopende import, of None. Met vergrendel FOR UPDATE: bevestigen, koppelen en annuleren
    wachten dan op elkaar."""
    q = select(Bezettingsimport).where(Bezettingsimport.verloopt_op > func.now())
    if vergrendel:
        q = q.with_for_update().execution_options(populate_existing=True)
    return db.session.scalar(q)


def _lopend_of_fout(vergrendel=True):
    imp = lopend(vergrendel)
    if imp is None:
        db.session.rollback()
        raise Regelfout("Er loopt geen bezettingsimport, of die is verlopen. Upload het bestand opnieuw.")
    return imp


def uploaden(data, actor):
    """Leest het bestand en bewaart het als lopende import. Een bestand met een fout in de opbouw
    (CsvFout) of een andere lopende import wordt geweigerd; de fouten per regel (onbekende plaats,
    bootsoort, eigenaar) staan in het overzicht."""
    verlopen_opruimen()
    if lopend() is not None:
        raise Regelfout("Er loopt al een bezettingsimport. Bevestig of annuleer die eerst.")
    rijen, meldingen = csvbestand.lees(data, KOLOMMEN)
    if meldingen:
        raise CsvFout(meldingen)
    if not rijen:
        raise Regelfout("Het bestand bevat geen regels met een bezette plaats.")
    db.session.add(Bezettingsimport(
        beheerder_id=actor.id, verloopt_op=datetime.now(UTC) + VERLOOP, keuzes={},
        regels=[{"regel": nr, **cel} for nr, cel in rijen]))
    try:
        db.session.commit()
    except IntegrityError as fout:
        db.session.rollback()
        if fout.orig.diag.constraint_name != "bezettingsimport_enige_key":
            raise
        raise Regelfout("Er loopt al een bezettingsimport. Bevestig of annuleer die eerst.") from None


def annuleren(actor):
    imp = _lopend_of_fout()
    db.session.delete(imp)
    db.session.commit()


def koppelen(keuzes, actor):
    """Slaat de keuzes op: {regelnummer: "" | "overslaan" | "club" | id van een actief lid} voor de
    eigenaar en {"soort-<regelnummer>": "" | "overslaan" | id van een soort die de plaats toelaat}
    voor de bootsoort (#202). Alles wat er niet in staat vervalt, behalve de eigenaar van een regel
    die bij de vorige opslag via de soortlijst was overgeslagen: het scherm toonde die lijst niet.
    Een onbekende regel, lid of soort weigert alles."""
    imp = _lopend_of_fout()
    regels = {str(r["regel"]): r for r in imp.regels}
    actief = {str(lid.id) for lid in leden.actieve_leden()}
    rekken, plaatsen = _rekken_en_plaatsen({})
    schoon = {}
    for sleutel, waarde in keuzes.items():
        if sleutel in regels:
            geldig = not waarde or waarde in {"overslaan", "club"} | actief
        elif sleutel.startswith(SOORT) and sleutel.removeprefix(SOORT) in regels:
            p = _plaats_zoeken(regels[sleutel.removeprefix(SOORT)]["plaats"], rekken, plaatsen)
            geldig = not waarde or waarde == "overslaan" or (
                p is not None and waarde in {str(s.id) for s in p.bootsoorten})
        else:
            geldig = False
        if not geldig:
            db.session.rollback()
            raise Regelfout("De keuzes kloppen niet meer. Ververs de pagina en probeer het opnieuw.")
        if waarde:
            schoon[sleutel] = waarde
    # Was een regel via de soortlijst overgeslagen, dan stond de eigenaarlijst niet op het scherm en is
    # er geen eigenaar gepost; de eerder gekozen eigenaar blijft dan staan (toets Design System).
    vorige = imp.keuzes or {}
    for regel, waarde in vorige.items():
        if regel in regels and regel not in keuzes and vorige.get(SOORT + regel) == "overslaan" \
                and waarde in {"overslaan", "club"} | actief:
            schoon[regel] = waarde
    imp.keuzes = schoon
    db.session.commit()


# Beoordelen


@dataclass
class Uitkomst:
    """Wat er met één regel gebeurt. tekst is wat in het bestand stond, voor het scherm."""

    regel: int
    tekst: dict
    uitkomst: str = ""
    melding: str = ""
    keuze: str = ""  # de keuze voor de eigenaar: overslaan, club of een lid-id
    soortkeuze: str = ""  # de keuze voor de bootsoort: overslaan of een soort-id (#202)
    soortlijst: bool = False  # toon de lijst voor de bootsoort
    eigenaar_open: bool = False  # de eigenaar is niet te koppelen: toon de lijst voor de eigenaar
    plaats: Plaats | None = None
    boot: Boot | None = None
    soort: Bootsoort | None = None
    lid: Lid | None = None
    club: bool = False
    onbekend: bool = False  # geen eigenaar in het bestand (#204)
    via: str = ""  # lidnummer, koppeling, naam, keuze of leeg: hoe de eigenaar is gevonden
    bewoner: Boot | None = None  # de boot die nu op de plaats ligt en niet de boot uit het bestand is
    herkomst: Plaats | None = None  # de plaats waar de boot uit het bestand nu ligt
    nieuw: bool = False


def _plaats_zoeken(code, rekken, plaatsen):
    delen = code.rsplit("/", 2)
    if len(delen) != 3 or not _GETAL.fullmatch(delen[1]) or not _GETAL.fullmatch(delen[2]):
        return None
    rek = rekken.get(delen[0].lower())
    return plaatsen.get((rek.id, int(delen[1]), int(delen[2]))) if rek else None


def _soort_zoeken(naam, soorten):
    """Precies zoals de applicatie hem schrijft, of zonder verschil in hoofdletters als dat maar
    één soort geeft (zoals bij de rekindeling)."""
    exact = [s for s in soorten if s.naam == naam]
    if exact:
        return exact[0]
    gevonden = [s for s in soorten if s.naam.lower() == naam.lower()]
    return gevonden[0] if len(gevonden) == 1 else None


def _rekken_en_plaatsen(opties):
    rekken = {r.naam.lower(): r for r in db.session.scalars(select(Rek).execution_options(**opties))}
    plaatsen = {(p.rek_id, p.verdieping, p.vak): p for p in db.session.scalars(
        select(Plaats).options(selectinload(Plaats.bootsoorten)).execution_options(**opties))}
    return rekken, plaatsen


def beoordeel(imp, vers=False):
    """Geeft per regel van de import een Uitkomst (ADR-014 §3), uit de huidige stand van de
    database en de keuzes. Verandert niets. vers=True leest de rijen opnieuw (na het vergrendelen)."""
    opties = {"populate_existing": vers}
    w = SimpleNamespace(plaats_op={}, boot_op={}, leden_per_naam={}, boten_per_naam={})
    w.rekken, w.plaatsen = _rekken_en_plaatsen(opties)
    alle_boten = db.session.scalars(select(Boot).execution_options(**opties)).all()
    w.boten_per_id = {b.id: b for b in alle_boten}
    for b in alle_boten:
        w.boten_per_naam.setdefault((b.naam.lower(), b.lid_id, b.clubboot), []).append(b)
    w.plaats_van_boot = {p.boot_id: p for p in w.plaatsen.values() if p.boot_id is not None}
    w.soorten = indeling.bootsoorten()
    alle_leden = db.session.scalars(select(Lid)).all()
    w.leden_per_id = {lid.id: lid for lid in alle_leden}
    w.leden_per_nummer = {lid.lidnummer: lid for lid in alle_leden}
    for lid in alle_leden:
        w.leden_per_naam.setdefault(lid.naam, []).append(lid)
    w.koppelingen = {k.naam: k for k in db.session.scalars(select(Naamkoppeling))}

    uitkomsten = []
    for r in imp.regels:
        nr = str(r["regel"])
        u = Uitkomst(r["regel"], {k: r[k] for k in KOLOMMEN}, keuze=imp.keuzes.get(nr, ""),
                     soortkeuze=imp.keuzes.get(SOORT + nr, ""))
        uitkomsten.append(u)
        if "overslaan" in (u.keuze, u.soortkeuze):
            u.uitkomst = OVERGESLAGEN
            u.soortlijst = u.soortkeuze == "overslaan"  # de lijst waarin de keuze staat blijft zichtbaar
        else:
            _beoordeel_regel(u, w)
    return uitkomsten


def _fout(u, melding):
    u.uitkomst, u.melding = FOUT, melding


def _eigenaar(u, w):
    """Volgorde (ADR-014 §3): keuze, het woord clubboot zonder bekend lidnummer, leeg is onbekend,
    lidnummer, onthouden koppeling, exacte naam. Zonder precies één treffer blijft het resultaat leeg (te koppelen)."""
    naam, nummer = u.tekst["eigenaar"], u.tekst["lidnummer"]
    if u.keuze == "club":
        u.club, u.via = True, "keuze"
    elif u.keuze:
        u.lid, u.via = w.leden_per_id.get(int(u.keuze)), "keuze"
    elif naam.lower() == CLUBBOOT and nummer not in w.leden_per_nummer:  # een lid "clubboot" koppelt op nummer (#214)
        u.club = True
    elif not naam and not nummer:
        u.onbekend = True
    elif nummer in w.leden_per_nummer:
        u.lid, u.via = w.leden_per_nummer[nummer], "lidnummer"
    elif naam in w.koppelingen:
        k = w.koppelingen[naam]
        u.lid, u.club, u.via = w.leden_per_id.get(k.lid_id), k.clubboot, "koppeling"
    elif len(w.leden_per_naam.get(naam, ())) == 1:
        u.lid, u.via = w.leden_per_naam[naam][0], "naam"


def _beoordeel_regel(u, w):
    t = u.tekst
    if not t["plaats"]:
        u.soortlijst = True  # alleen Regel overslaan
        return _fout(u, "De plaats ontbreekt.")
    if not 1 <= len(t["boot"]) <= BOOT_MAX:
        return _fout(u, f"De naam van de boot ontbreekt of is langer dan {BOOT_MAX} tekens.")
    if not t["bootsoort"]:
        return _fout(u, "De bootsoort ontbreekt.")
    if len(t["eigenaar"]) > EIGENAAR_MAX:
        return _fout(u, f"De eigenaar is langer dan {EIGENAAR_MAX} tekens.")
    if t["lidnummer"] and not leden.LIDNUMMER.fullmatch(t["lidnummer"]):
        return _fout(u, "Het lidnummer is ongeldig.")
    if t["eigenaar"].lower() == CLUBBOOT and t["lidnummer"] and t["lidnummer"] not in w.leden_per_nummer:
        return _fout(u, "Een clubboot heeft geen lidnummer. Maak het lidnummer leeg.")
    u.plaats = _plaats_zoeken(t["plaats"], w.rekken, w.plaatsen)
    if u.plaats is None:
        u.soortlijst = True  # alleen Regel overslaan
        return _fout(u, f"Plaats {_kort(t['plaats'])} bestaat niet.")
    if u.soortkeuze:  # externe invoer: alleen een soort die de plaats nu toelaat
        u.soortlijst = True
        u.soort = next((s for s in u.plaats.bootsoorten if str(s.id) == u.soortkeuze), None)
        fout = "De gekozen bootsoort bestaat niet meer of past niet op de plaats. Kies opnieuw."
    else:
        u.soort = _soort_zoeken(t["bootsoort"], w.soorten)
        u.soortlijst = u.soort is None
        fout = (f"De bootsoort {_kort(t['bootsoort'])} bestaat niet of is dubbelzinnig, "
                "kies hem in de lijst.")
    if u.soort is None:
        _eigenaar(u, w)  # ook de eigenaar beoordelen: beide keuzes kunnen nodig zijn (#202)
        u.eigenaar_open = u.lid is None and not u.club and not u.onbekend
        return _fout(u, f"{fout} {EIGENAAR_ONGEKOPPELD}" if u.eigenaar_open else fout)
    if u.plaats.id in w.plaats_op:
        return _fout(u, f"Plaats {u.plaats.code} staat al op regel {w.plaats_op[u.plaats.id]}.")
    w.plaats_op[u.plaats.id] = u.regel
    _eigenaar(u, w)
    if u.lid is None and not u.club and not u.onbekend:
        u.eigenaar_open = True
        u.uitkomst = TE_KOPPELEN
        u.melding = EIGENAAR_ONGEKOPPELD
        return None
    sleutel = (t["boot"].lower(), u.lid.id if u.lid else None, u.club)
    gevonden = w.boten_per_naam.get(sleutel, [])
    if len(gevonden) > 1:
        return _fout(u, "Er zijn meer boten met deze naam en eigenaar.")
    if sleutel in w.boot_op:
        return _fout(u, f"Deze boot staat al op regel {w.boot_op[sleutel]}.")
    w.boot_op[sleutel] = u.regel
    u.boot = gevonden[0] if gevonden else None
    if u.boot is not None and u.boot.bootsoort_id != u.soort.id:
        return _fout(u, f"Boot {u.boot.naam} bestaat al als een {u.boot.bootsoort.naam.lower()}. "
                        "De import wijzigt geen boot.")
    u.nieuw = u.boot is None
    u.herkomst = w.plaats_van_boot.get(u.boot.id) if u.boot else None
    if u.boot is not None and u.herkomst is u.plaats:
        u.uitkomst = "ongewijzigd"
        return None
    if u.lid is not None and leden.is_oud_lid(u.lid):
        return _fout(u, f"{u.lid.naam} is oud-lid. De boot krijgt geen plaats en er komt geen "
                        "nieuwe boot.")
    try:
        toewijzing.controleer_past(u.plaats, u.boot.naam if u.boot else t["boot"], u.soort,
                                   u.club)
    except Regelfout as f:
        return _fout(u, str(f))
    bewoner = w.boten_per_id.get(u.plaats.boot_id)
    u.bewoner = bewoner
    gaat_weg = f"{bewoner.naam} gaat van de plaats. " if bewoner else ""
    komt_van = f"Komt van {u.herkomst.code}." if u.herkomst else ""
    u.melding = (gaat_weg + komt_van).strip()
    u.uitkomst = ("nieuwe boot" if u.nieuw else "overschrijven" if bewoner
                  else "verplaatsen" if u.herkomst else "toewijzen")
    return None


def _betrokken(uitkomsten):
    """De boten en plaatsen die bevestigen vergrendelt: boot uit het bestand en huidige bewoner,
    plaats en herkomst (ADR-014 §3)."""
    boot_ids, plaats_ids = set(), set()
    for u in uitkomsten:
        if u.uitkomst in GEEN_ACTIE + BLOKKEERT:
            continue
        plaats_ids.add(u.plaats.id)
        boot_ids |= {b.id for b in (u.boot, u.bewoner) if b}
        if u.herkomst:
            plaats_ids.add(u.herkomst.id)
    return boot_ids, plaats_ids


def overzicht():
    """Voor het scherm: de lopende import met de uitkomst per regel, of None."""
    verlopen_opruimen()
    imp = lopend()
    if imp is None:
        return None
    uitkomsten = beoordeel(imp)
    telling = {}
    for u in uitkomsten:
        telling[u.uitkomst] = telling.get(u.uitkomst, 0) + 1
    return {"lopend": imp, "uitkomsten": uitkomsten, "leden": leden.actieve_leden(),
            "telling": telling, "kan_bevestigen": not any(u.uitkomst in BLOKKEERT for u in uitkomsten)}


# Bevestigen


def _vergrendel(boot_ids, plaats_ids):
    """Eerst de boten, dan de plaatsen, beide oplopend op id: twee imports (of een import en
    toewijzen of boot_wijzigen, die boot en dan plaats vergrendelen) lopen niet vast."""
    db.session.scalars(select(Boot).where(Boot.id.in_(boot_ids)).order_by(Boot.id)
                       .with_for_update(of=Boot).execution_options(populate_existing=True)).all()
    db.session.scalars(select(Plaats).where(Plaats.id.in_(plaats_ids)).order_by(Plaats.id)
                       .with_for_update(of=Plaats).execution_options(populate_existing=True)).all()


def _blokkade(uitkomsten):
    if any(u.uitkomst in BLOKKEERT for u in uitkomsten):
        raise Regelfout("De import is niet uitgevoerd: er zijn regels te koppelen of met een fout. "
                        "Kijk in het overzicht, los ze op of sla ze over.")


def bevestigen(actor):
    """Voert de lopende import uit in één transactie, of niets (ADR-014 §3): nieuwe boten, dan
    vergrendelen, elke regel opnieuw controleren, alle vrijgaven, alle toewijzingen, koppelingen
    onthouden, de import weg en één logregel. Geeft de aantallen."""
    try:
        imp = _lopend_of_fout()
        eerste = beoordeel(imp)
        _blokkade(eerste)
        boot_ids, plaats_ids = _betrokken(eerste)
        for u in eerste:
            if u.uitkomst == "nieuwe boot":
                b = boten._boot_aanmaken(u.tekst["boot"], u.soort.id, u.lid.id if u.lid else None,
                                         None, actor, u.club)
                boot_ids.add(b.id)
        _vergrendel(boot_ids, plaats_ids)
        uitkomsten = beoordeel(imp, vers=True)
        _blokkade(uitkomsten)
        nu_boten, nu_plaatsen = _betrokken(uitkomsten)
        if not (nu_boten <= boot_ids and nu_plaatsen <= plaats_ids):
            raise Regelfout("Er is intussen iets veranderd aan de boten of plaatsen. Probeer het "
                            "opnieuw.")
        acties = sorted((u for u in uitkomsten if u.uitkomst not in GEEN_ACTIE),
                        key=lambda u: u.plaats.id)
        vrij = {p.id: p for u in acties for p in (u.herkomst, u.plaats if u.bewoner else None) if p}
        try:
            for plaats_id in sorted(vrij):
                if vrij[plaats_id].boot_id is not None:
                    toewijzing._vrijgeven(vrij[plaats_id], actor)
            db.session.flush()  # eerst weg, dan erbij: de plaats van een boot is uniek
            for u in acties:
                toewijzing._toewijzen(u.plaats, u.boot, actor)
        except Regelfout:
            # De regels zijn net gecontroleerd; de melding van de kern noemt een boot uit het bestand.
            raise Regelfout("De import is niet uitgevoerd: een regel kon niet worden uitgevoerd. "
                            "Kijk in het overzicht en probeer het opnieuw.") from None
        aantallen = _afronden(imp, eerste, uitkomsten, actor)
    except Exception:
        db.session.rollback()
        raise
    db.session.commit()
    return aantallen


def _afronden(imp, eerste, uitkomsten, actor):
    """Onthoudt de koppelingen, verwijdert de import en schrijft het technische log. De aantallen
    volgen het overzicht dat de beheerder zag (eerste): een nieuwe boot is bij de tweede
    beoordeling al een bestaande."""
    koppelingen = {k.naam: k for k in db.session.scalars(
        select(Naamkoppeling).with_for_update())}
    onthouden = 0
    for u in uitkomsten:
        naam = u.tekst["eigenaar"]
        if u.uitkomst == OVERGESLAGEN or not naam:
            continue
        k = koppelingen.get(naam)
        if u.via == "keuze":
            if k is None:
                k = koppelingen[naam] = Naamkoppeling(naam=naam)
                db.session.add(k)
            k.lid_id, k.clubboot = (u.lid.id if u.lid else None), u.lid is None
            k.gebruikt_op = func.now()
            onthouden += 1
        elif u.via == "koppeling":
            k.gebruikt_op = func.now()
    aantallen = {
        "regels": len(eerste), "nieuw": sum(u.uitkomst == "nieuwe boot" for u in eerste),
        "toegewezen": sum(u.uitkomst == "toewijzen" for u in eerste),
        "overschreven": sum(u.uitkomst == "overschrijven" for u in eerste),
        "verplaatst": sum(u.uitkomst == "verplaatsen" for u in eerste),
        "ongewijzigd": sum(u.uitkomst == "ongewijzigd" for u in eerste),
        "overgeslagen": sum(u.uitkomst == OVERGESLAGEN for u in eerste),
        "koppelingen": onthouden}
    db.session.delete(imp)
    log.schrijf(actor, "bezetting.geimporteerd", [], aantallen)
    return aantallen


# Onthouden koppelingen


def koppelingen():
    return db.session.scalars(select(Naamkoppeling).options(selectinload(Naamkoppeling.lid))
                              .order_by(Naamkoppeling.naam, Naamkoppeling.id)).all()


def koppeling_verwijderen(koppeling_id, actor):
    k = db.session.get(Naamkoppeling, koppeling_id, with_for_update=True)
    if k is None:
        db.session.rollback()
        raise Regelfout("Deze koppeling bestaat niet.")
    # Alleen een verwijzing, geen naam uit een bestand (ADR-014 §3, Loggen).
    log.schrijf(actor, "naamkoppeling.verwijderd", [f"lid:{k.lid_id}" if k.lid_id else "clubboot"])
    db.session.delete(k)
    db.session.commit()
