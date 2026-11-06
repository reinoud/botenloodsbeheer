"""CSV-bestanden van beheerders (ADR-014 §1): inlezen met grenzen, commentaar, BOM en
scheidingsteken, en schrijven met formulebescherming. De import van de rekindeling (#157) en
van de bezetting (#158) gebruiken beide dezelfde functies. Een bestand is externe invoer."""

import csv
import io
import re
import unicodedata

from app.domein import Regelfout

MAX_BYTES = 256 * 1024
MAX_REGELS = 2000
MAX_MELDINGEN = 50

# Een cel die een spreadsheet als formule leest, krijgt een ' ervoor. De import haalt precies die
# ' weg. Een cel die al met ' + teken begint, krijgt er ook een, zodat een rondgang niets verandert.
_FORMULE = re.compile(r"'*[=+\-@\t\r]")
_GENEUTRALISEERD = re.compile(r"'+[=+\-@\t\r]")


class CsvFout(Regelfout):
    """Een geweigerd bestand. `regels` zijn de meldingen, per foute regel met het regelnummer."""

    def __init__(self, regels):
        regels = list(regels)
        if len(regels) > MAX_MELDINGEN:
            regels = regels[:MAX_MELDINGEN] + [f"En nog {len(regels) - MAX_MELDINGEN} meldingen."]
        super().__init__(" ".join(["Het bestand is niet geïmporteerd. Er is niets veranderd.",
                                   *regels]))
        self.regels = regels


def veilig(waarde):
    """De tekst voor een cel in een export: een formule wordt tekst."""
    waarde = str(waarde)
    return "'" + waarde if _FORMULE.match(waarde) else waarde


def schrijf(rijen):
    """De rijen als UTF-8 met BOM, puntkomma's en regeleinden zoals Excel ze verwacht."""
    uit = io.StringIO()
    schrijver = csv.writer(uit, delimiter=";", lineterminator="\r\n")
    for rij in rijen:
        schrijver.writerow([veilig(cel) for cel in rij])
    return ("﻿" + uit.getvalue()).encode("utf-8")


def _leeg(rij):
    return not any(cel.strip() for cel in rij)


def lees(data, kolommen):
    """Geeft (rijen, meldingen): rijen is [(regelnummer, {kolom: tekst})] zonder commentaar en
    lege regels, in de volgorde van het bestand, de cellen getrimd en zonder de ' van een
    geneutraliseerde formule. Meldingen zijn fouten per regel (kolomtelling, stuurtekens). Een
    fout in het bestand zelf (grootte, codering, scheidingsteken, kolommen) is een CsvFout."""
    if len(data) > MAX_BYTES:
        raise CsvFout([f"Het bestand is groter dan {MAX_BYTES // 1024} kB."])
    if b"\0" in data:
        raise CsvFout(["Dit is geen CSV-bestand."])
    try:
        tekst = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise CsvFout(["Het bestand is geen UTF-8. Sla het op als CSV UTF-8."]) from None
    if len(tekst.splitlines()) > MAX_REGELS:
        raise CsvFout([f"Het bestand heeft meer dan {MAX_REGELS} regels."])

    lezer = csv.reader(io.StringIO(tekst, newline=""), delimiter=";", strict=True)
    kop, rijen, meldingen, vorige = None, [], [], 0
    try:
        for rij in lezer:
            regel, vorige = vorige + 1, lezer.line_num  # een veld met regeleinde beslaat meer regels
            if _leeg(rij) or rij[0].startswith("#"):
                continue
            if kop is None:
                kop = [cel.strip().lower() for cel in rij]
                _controleer_kop(kop, kolommen, regel)
                continue
            if len(rij) != len(kop):
                meldingen.append(f"Regel {regel}: {len(kop)} kolommen verwacht, {len(rij)} gevonden.")
            elif any(unicodedata.category(t) == "Cc" for cel in rij for t in cel.strip()):
                meldingen.append(f"Regel {regel}: een stuurteken of regeleinde in een veld "
                                 "is niet toegestaan.")
            else:
                rijen.append((regel, dict(zip(kop, (_ontdoe(cel) for cel in rij), strict=True))))
    except csv.Error:
        raise CsvFout([(f"Regel {lezer.line_num}: het bestand is niet te lezen als CSV, "
                        "controleer de aanhalingstekens.")]) from None
    if kop is None:
        raise CsvFout(["Het bestand heeft geen kopregel."])
    return rijen, meldingen


def _ontdoe(cel):
    cel = cel.strip()
    return cel[1:] if _GENEUTRALISEERD.match(cel) else cel


def _controleer_kop(kop, kolommen, regel):
    if len(kop) == 1:
        raise CsvFout([(f"Regel {regel}: de kopregel heeft geen puntkomma. Gebruik een "
                        "puntkomma als scheidingsteken.")])
    ontbreekt = [k for k in kolommen if k not in kop]
    onbekend = [k for k in dict.fromkeys(kop) if k not in kolommen][:5]
    if ontbreekt or onbekend or len(set(kop)) != len(kop):
        delen = ([f"kolom ontbreekt: {', '.join(ontbreekt)}"] if ontbreekt else []) \
            + ([f"onbekende kolom: {', '.join(t[:30] for t in onbekend)}"] if onbekend else []) \
            + (["een kolom staat er twee keer in"] if len(set(kop)) != len(kop) else [])
        raise CsvFout([(f"Regel {regel}: de kopregel klopt niet ({'; '.join(delen)}). "
                        f"Verwacht: {';'.join(kolommen)}.")])
