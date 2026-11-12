"""Bron e-boekhouden (ADR-004, ADR-012): de enige code die met e-boekhouden praat, via SOAP met zeep.

Drie aanroepen: OpenSession, GetRelaties en UpdateRelatie, en CloseSession na afloop. De WSDL
staat als kopie in het image (eboekhouden.wsdl), dus er is bij het starten geen netwerk nodig en
zeep schrijft niets naar schijf (geen cache). De WSDL noemt een http-adres; het adres van de
dienst staat hier vast op https, anders gaan de inloggegevens onversleuteld over de lijn.
Geen tekst van e-boekhouden gaat naar de API of het log: een fout wordt een reden uit de vaste
lijst, het log noemt hooguit het soort fout. zeep wordt pas bij het eerste gebruik geladen, zodat
de rest van de container (en de unittests van de applicatie) het zonder doen.
"""

import json
import logging
from contextlib import contextmanager
from pathlib import Path

from koppeling.bronnen import Ledenbron, LedenbronFout

log = logging.getLogger("koppeling")
# zeep logt op DEBUG de volledige verzoeken, dus ook de inloggegevens; nooit in het log.
logging.getLogger("zeep").setLevel(logging.WARNING)

WSDL = Path(__file__).with_name("eboekhouden.wsdl")
ADRES = "https://soap.e-boekhouden.nl/soap.asmx"
BINDING = "{http://www.e-boekhouden.nl/soap}soapAppSoap"
LID_IN_DEF2 = ("actief", "opgezegd")  # Def2 begint met de soort relatie; "inactief" is geen lid
TIMEOUT = 30
MAX_ACHTEREEN = 3  # na zoveel fouten achter elkaar stopt het schrijven, zodat de lus niet blokkeert


def _reden(fout):
    """De reden uit de vaste lijst van de API (BLB-006) bij een fout van zeep of requests."""
    import requests
    import zeep.exceptions

    if isinstance(fout, zeep.exceptions.TransportError):
        # 200 met een antwoord dat geen XML is: onleesbaar. 401 en 403: geweigerd. De rest van de
        # HTTP-fouten (502, 503, ...) betekent dat de dienst er niet is.
        return {200: "bron_onleesbaar", 401: "bron_geweigerd", 403: "bron_geweigerd"}.get(
            fout.status_code, "bron_onbereikbaar")
    if isinstance(fout, requests.RequestException):
        return "bron_onbereikbaar"
    return "bron_onleesbaar"


def _tekst(waarde):
    return (waarde or "").strip() or None


class EboekhoudenBron(Ledenbron):
    kan_terugschrijven = True

    def __init__(self, username, code1, code2, adres=ADRES):
        self._inlog = {"Username": username, "SecurityCode1": code1, "SecurityCode2": code2}
        self._code2, self._adres, self._service = code2, adres, None

    def _verbind(self):
        from zeep import Client, Transport

        client = Client(str(WSDL), transport=Transport(cache=None, timeout=TIMEOUT,
                                                       operation_timeout=TIMEOUT))
        return client.create_service(BINDING, self._adres)

    @contextmanager
    def _sessie(self):
        """Geeft (service, sessie-id) en sluit de sessie weer. Gooit LedenbronFout."""
        sessie = None
        try:
            if self._service is None:
                self._service = self._verbind()
            antwoord = self._service.OpenSession(**self._inlog)
            self._controleer(antwoord["ErrorMsg"])
            sessie = antwoord["SessionID"]
            if not sessie:
                raise LedenbronFout("bron_geweigerd")
            yield self._service, sessie
        except LedenbronFout:
            raise
        except Exception as fout:  # noqa: BLE001  alles wordt een reden; het log noemt het soort
            log.warning("e-boekhouden: %s", type(fout).__name__)
            raise LedenbronFout(_reden(fout)) from None
        finally:
            if sessie:
                try:
                    self._service.CloseSession(SessionID=sessie)
                except Exception as fout:  # noqa: BLE001  sluiten is hoffelijkheid, geen fout
                    log.warning("e-boekhouden sluiten: %s", type(fout).__name__)

    @staticmethod
    def _controleer(fout):
        """Een cError met een foutcode is een weigering door e-boekhouden."""
        if fout is not None and fout["LastErrorCode"]:
            raise LedenbronFout("bron_geweigerd")

    def _leden(self, service, sessie):
        """De relaties die lid zijn, als de zeep-objecten zoals e-boekhouden ze gaf."""
        from zeep.xsd import SkipValue

        antwoord = service.GetRelaties(
            SessionID=sessie, SecurityCode2=self._code2,
            cFilter={"Trefwoord": SkipValue, "Code": SkipValue, "ID": SkipValue})
        self._controleer(antwoord["ErrorMsg"])
        relaties = antwoord["Relaties"]["cRelatie"] if antwoord["Relaties"] is not None else []
        soort = lambda r: (r["Def2"] or "").strip().lower()  # defensief tegen tikfouten (#226)
        # opgezegd zonder opzegdatum (Def7) zou als actief lid binnenkomen; overslaan (#221)
        return [r for r in relaties if soort(r).startswith(LID_IN_DEF2)
                and not (soort(r).startswith("opgezegd") and _tekst(r["Def7"]) is None)]

    def haal_leden(self):
        """Besluit 1 van #178: lidnummer, naam, lid_sinds en opzegdatum; geen adres, telefoon of
        e-mail. Lid is een relatie waarvan Def2 begint met "actief", of met "opgezegd" en die een
        opzegdatum in Def7 heeft (#221)."""
        with self._sessie() as (service, sessie):
            return [{"lidnummer": _tekst(r["Code"]), "naam": _tekst(r["Bedrijf"]),
                     "lid_sinds": _tekst(r["Def3"]), "opzegdatum": _tekst(r["Def7"])}
                    for r in self._leden(service, sessie)]

    def schrijf_bootaantallen(self, aantallen):
        """Zet per lid Def10 op de aantallen als JSON-tekst (besluit 2 van #178). Het record komt
        vers uit GetRelaties en gaat ongewijzigd terug, op Def10 na. Geeft de aantallen
        geschreven, ongewijzigd, niet_gevonden en fout."""
        uitkomst = {"geschreven": 0, "ongewijzigd": 0, "niet_gevonden": 0, "fout": 0}
        achtereen = 0
        with self._sessie() as (service, sessie):
            leden = {_tekst(r["Code"]): r for r in self._leden(service, sessie)}
            for rij in aantallen:
                if achtereen >= MAX_ACHTEREEN:
                    uitkomst["fout"] += 1
                    continue
                relatie = leden.get(str(rij["lidnummer"]).strip())
                waarde = json.dumps(rij["aantallen"], ensure_ascii=False)
                if relatie is None:
                    uitkomst["niet_gevonden"] += 1
                elif (relatie["Def10"] or "") == waarde:
                    uitkomst["ongewijzigd"] += 1
                else:
                    relatie["Def10"] = waarde
                    try:
                        self._controleer(service.UpdateRelatie(
                            SessionID=sessie, SecurityCode2=self._code2, oRel=relatie))
                    except Exception as fout:  # noqa: BLE001  telt als fout; geen herhaling
                        log.warning("e-boekhouden: %s", type(fout).__name__)
                        uitkomst["fout"] += 1
                        achtereen += 1
                        continue
                    uitkomst["geschreven"] += 1
                achtereen = 0
        return uitkomst
