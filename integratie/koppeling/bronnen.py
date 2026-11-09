"""Ledenbron (ADR-004): de enige module die met het externe systeem praat.

Een bron levert ruwe records; validatie en opslag zitten achter de API, zodat elke bron en elke
vervangende container dezelfde regels krijgt. Een nieuwe bron is een klasse hier en een waarde
voor LEDENBRON.
"""

import json


class LedenbronFout(Exception):
    """Storing van de bron. De tekst is een reden uit de vaste lijst van de API (BLB-006)."""


class NietBeschikbaar(Exception):
    pass


class Ledenbron:
    kan_terugschrijven = False

    def haal_leden(self):
        """Lijst van dicts met lidnummer, naam, lid_sinds en opzegdatum
        (datums als JJJJ-MM-DD). Gooit LedenbronFout."""
        raise NotImplementedError

    def schrijf_bootaantallen(self, aantallen):
        """aantallen: de lijst van GET /bootaantallen. Geeft de aantallen geschreven, ongewijzigd,
        niet_gevonden en fout. Een bron die niet kan terugschrijven gooit NietBeschikbaar."""
        raise NietBeschikbaar("Deze bron kan niet terugschrijven.")


class StubBron(Ledenbron):
    """Leest leden uit een JSON-bestand: alleen voor ontwikkeling en tests."""

    def __init__(self, pad):
        self.pad = pad

    def haal_leden(self):
        try:
            with open(self.pad, encoding="utf-8") as f:
                records = json.load(f)
        except OSError:
            raise LedenbronFout("bron_onbereikbaar") from None
        except ValueError:
            raise LedenbronFout("bron_onleesbaar") from None
        if not isinstance(records, list):
            raise LedenbronFout("bron_onleesbaar")
        return records


EBOEKHOUDEN_INLOG = ("EBOEKHOUDEN_USERNAME", "EBOEKHOUDEN_CODE1", "EBOEKHOUDEN_CODE2")


def kies(omgeving):
    """De bron uit LEDENBRON, of None zonder bron (BLB-007)."""
    naam = omgeving.get("LEDENBRON", "")
    if naam == "":
        return None
    if naam == "stub":
        return StubBron(omgeving.get("LEDENBRON_STUB_BESTAND", "/data/leden.json"))
    if naam == "eboekhouden":
        from koppeling.eboekhouden import EboekhoudenBron  # zeep pas bij gebruik (ADR-012)

        inlog = [omgeving.get(v, "").strip() for v in EBOEKHOUDEN_INLOG]
        if not all(inlog):
            raise ValueError(f"{', '.join(EBOEKHOUDEN_INLOG)} zijn verplicht bij "
                             "LEDENBRON=eboekhouden")
        return EboekhoudenBron(*inlog)
    raise ValueError("LEDENBRON moet leeg zijn, stub of eboekhouden")
