"""Integratiecontainer (ADR-012): haalt de leden uit de bron en stuurt ze naar de API.

Alleen de standaardbibliotheek en alleen de aanroepen uit docs/beheer/integratiecontainer.md.
Elke ronde: is er een importverzoek, of is SYNC_TIJDSTIP gepasseerd zonder geslaagde import die
dag, dan importeert hij. Na een fout hooguit één geplande poging per uur; een verzoek van een
beheerder wacht niet (#28). De log bevat nooit het token,
inloggegevens van de bron of gegevens van leden.
"""

import json
import logging
import urllib.error
import urllib.request
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from koppeling import bronnen

NIEUWE_POGING = timedelta(hours=1)
# De grenzen van PUT /api/v1/leden; daarboven meldt de container de bron als onleesbaar.
MAX_RECORDS = 5000
MAX_BYTES = 2 * 1024 * 1024

log = logging.getLogger("koppeling")


class ApiFout(Exception):
    """Een aanroep mislukte; de tekst is alleen de HTTP-status of het soort fout."""


def instellingen(omgeving):
    try:
        tijdstip = time.fromisoformat(omgeving.get("SYNC_TIJDSTIP", "03:00"))
    except ValueError:
        raise ValueError("SYNC_TIJDSTIP moet een tijd zijn als 03:00") from None
    return {
        "api_url": omgeving.get("API_URL", "http://nginx:8081/api/v1").rstrip("/"),
        "token_bestand": omgeving.get("API_TOKEN_FILE", "/run/secrets/api_token"),
        "tijdstip": tijdstip,
        "tz": ZoneInfo(omgeving.get("TZ", "Europe/Amsterdam")),
        "bron": bronnen.kies(omgeving),
    }


class Koppeling:
    def __init__(self, cfg):
        self.cfg = cfg
        self.geslaagd_op = None  # dag van de laatste geslaagde import
        self.fout_op = None
        self.fout_token = None
        self.fout_van_api = False

    def lees_token(self):
        """Bij elke ronde opnieuw, zodat een nieuw token geen herstart vraagt (BLB-039)."""
        try:
            with open(self.cfg["token_bestand"], encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            return ""

    def roep(self, token, methode, pad, gegevens=None):
        """Geeft het JSON-antwoord, of gooit ApiFout."""
        verzoek = urllib.request.Request(
            self.cfg["api_url"] + pad, method=methode, data=gegevens,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(verzoek, timeout=60) as antwoord:
                return json.loads(antwoord.read() or b"{}")
        except urllib.error.HTTPError as fout:
            raise ApiFout(f"HTTP {fout.code}") from None
        except (OSError, ValueError) as fout:  # URLError en time-out zijn OSError
            raise ApiFout(type(fout).__name__) from None

    def melden(self, token, reden):
        self.roep(token, "POST", "/leden/import-mislukt", json.dumps({"reden": reden}).encode())

    def importeer(self, token, nu):
        try:
            records = self.cfg["bron"].haal_leden()
            gegevens = json.dumps({"leden": records}).encode()
            if len(records) > MAX_RECORDS or len(gegevens) > MAX_BYTES:
                raise bronnen.LedenbronFout("bron_onleesbaar")
        except bronnen.LedenbronFout as fout:
            self.melden(token, str(fout))
            raise
        aantallen = self.roep(token, "PUT", "/leden", gegevens)
        self.geslaagd_op, self.fout_op = nu.date(), None
        # Alleen getallen; nooit gegevens van leden.
        log.info("Import geslaagd: %s", {k: v for k, v in aantallen.items() if type(v) is int})

    def ronde(self, nu=None):
        nu = nu or datetime.now(self.cfg["tz"])
        token = self.lees_token()
        if not token:
            log.warning("Geen token in %s; nieuwe poging over een minuut.",
                        self.cfg["token_bestand"])
            return
        # Een nieuw token mag meteen; met hetzelfde token na een fout pas na een uur een geplande
        # import. Een verzoek van een beheerder wacht niet (besluit 2026-10-31, #28).
        wachten = self.fout_op and nu - self.fout_op < NIEUWE_POGING and token == self.fout_token
        if wachten and self.fout_van_api:
            return  # het verzoek blijft open en een geweigerde aanroep komt in het log van de API
        try:
            verzoek = self.roep(token, "GET", "/leden/importverzoek").get("aangevraagd") is True
            gepland = (not wachten and nu.time() >= self.cfg["tijdstip"]
                       and self.geslaagd_op != nu.date())
            if verzoek or gepland:
                self.importeer(token, nu)
        except bronnen.LedenbronFout as fout:
            self._fout(nu, token, str(fout), van_api=False)
        except ApiFout as fout:
            # Een 409 sluit het verzoek (veiligheidsgrens) of een lopende import doet dat.
            self._fout(nu, token, str(fout), van_api=str(fout) != "HTTP 409")
        except Exception as fout:  # noqa: BLE001  de lus draait door; alleen het soort fout
            self._fout(nu, token, type(fout).__name__, van_api=True)

    def _fout(self, nu, token, tekst, van_api):
        self.fout_op, self.fout_token, self.fout_van_api = nu, token, van_api
        log.warning("Import mislukt (%s); nieuwe poging over een uur.", tekst)
