"""Integratiecontainer (BLB-006, 007, 039; ADR-004, ADR-012) met de stub en een nep-API, en de
opbouw van docker-compose.yml. Zonder database: de container kent alleen de API."""

import ast
import json
import logging
import os
import re
import subprocess
import sys
import threading
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
import yaml

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "integratie"))

from koppeling import ANTWOORD_MAX, MAX_BYTES, ApiFout, Koppeling, bronnen, instellingen

TZ = ZoneInfo("Europe/Amsterdam")
OCHTEND = datetime(2026, 10, 31, 10, 0, tzinfo=TZ)
TOKEN = "blb_" + "A" * 60
FIXTURE = ROOT / "tests/fixtures/leden.json"


class NepApi(ThreadingHTTPServer):
    """Legt elke aanroep vast en antwoordt met een vaste status per pad."""

    def __init__(self):
        super().__init__(("127.0.0.1", 0), Handler)
        self.aanroepen, self.verzoek, self.status, self.fout = [], False, {}, "Geen toegang."
        self.groot, self.vrij, self.klaar = False, threading.Event(), False
        self.bootaantallen = [{"lidnummer": "1001", "aantallen": {"Kajak": 1, "Surfski": 0}}]
        threading.Thread(target=self.serve_forever, daemon=True).start()

    @property
    def url(self):
        return f"http://127.0.0.1:{self.server_address[1]}/api/v1"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def _antwoord(self):
        lengte = int(self.headers.get("Content-Length") or 0)
        lichaam = json.loads(self.rfile.read(lengte)) if lengte else None
        pad = self.path.removeprefix("/api/v1")
        self.server.aanroepen.append((self.command, pad, self.headers["Authorization"], lichaam))
        status = self.server.status.get(pad, 201 if self.command == "POST" else 200)
        antwoord = {"/leden/importverzoek": {"aangevraagd": self.server.verzoek},
                    "/leden": {"ontvangen": len(lichaam["leden"]), "nieuw": 1} if pad == "/leden" else {},
                    "/bootaantallen": self.server.bootaantallen}.get(pad, {})
        tekst = json.dumps(antwoord if status < 400 else {"fout": self.server.fout}).encode()
        self.send_response(status)
        if self.server.groot:  # #109: te groot antwoord zonder lengte; de verbinding blijft open
            self.end_headers()
            try:
                self.wfile.write(b" " * (ANTWOORD_MAX + 1))
            except OSError:
                return  # de container sloot de verbinding al
            self.server.vrij.wait(5)
            self.server.klaar = True
            return
        if 300 <= status < 400:
            self.send_header("Location", self.server.locatie)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(tekst)))
        self.end_headers()
        self.wfile.write(tekst)

    do_GET = do_PUT = do_POST = _antwoord


@pytest.fixture
def api():
    server = NepApi()
    yield server
    server.vrij.set()
    server.shutdown()
    server.server_close()


@pytest.fixture
def koppeling(api, tmp_path):
    token = tmp_path / "api_token"
    token.write_text(TOKEN + "\n")
    cfg = instellingen({"API_URL": api.url, "API_TOKEN_FILE": str(token), "LEDENBRON": "stub",
                        "LEDENBRON_STUB_BESTAND": str(FIXTURE), "SYNC_TIJDSTIP": "03:00"})
    k = Koppeling(cfg)
    k.token = token
    return k


def paden(api):
    return [(methode, pad) for methode, pad, _a, _l in api.aanroepen]


def test_verzoek_stuurt_de_volledige_lijst_met_het_token(api, koppeling, caplog):
    """BLB-006 criterium 5, BLB-007 criterium 1, BLB-039 criterium 5: geen token of lid in de log."""
    api.verzoek = True
    koppeling.geslaagd_op = OCHTEND.date()  # alleen het verzoek telt
    with caplog.at_level(logging.INFO):
        koppeling.ronde(OCHTEND)
    assert paden(api) == [("GET", "/leden/importverzoek"), ("PUT", "/leden")]
    _m, _p, autorisatie, lichaam = api.aanroepen[1]
    assert autorisatie == f"Bearer {TOKEN}"
    assert lichaam["leden"] == json.loads(FIXTURE.read_text())
    log = caplog.text
    assert "Import geslaagd" in log and "'ontvangen': 210" in log
    for geheim in (TOKEN, TOKEN[4:12], "@example.org", lichaam["leden"][0]["naam"]):
        assert geheim not in log


def test_dagelijks_na_het_tijdstip_als_die_dag_nog_niets_slaagde(api, koppeling):
    """BLB-006 criterium 2."""
    koppeling.ronde(OCHTEND.replace(hour=2, minute=59))
    assert paden(api) == [("GET", "/leden/importverzoek")]  # te vroeg
    koppeling.ronde(OCHTEND.replace(hour=3))
    assert paden(api)[-1] == ("PUT", "/leden")
    koppeling.ronde(OCHTEND.replace(hour=4))
    assert paden(api)[-1] == ("GET", "/leden/importverzoek")  # vandaag al geslaagd
    koppeling.ronde(OCHTEND.replace(hour=3) + timedelta(days=1))
    assert paden(api)[-1] == ("PUT", "/leden")


@pytest.mark.parametrize("inhoud,reden", [(None, "bron_onbereikbaar"), ("{kapot", "bron_onleesbaar"),
                                          ('{"geen": "lijst"}', "bron_onleesbaar")],
                         ids=["ontbreekt", "kapot", "geen-lijst"])
def test_fout_van_de_bron_gemeld_en_hooguit_een_poging_per_uur(api, koppeling, tmp_path,
                                                               inhoud, reden):
    """BLB-006 criterium 3: reden uit de vaste lijst, geen PUT, daarna een uur geen geplande import."""
    bron = tmp_path / "leden.json"
    if inhoud is not None:
        bron.write_text(inhoud)
    koppeling.cfg["bron"] = bronnen.StubBron(str(bron))
    koppeling.ronde(OCHTEND)
    assert paden(api) == [("GET", "/leden/importverzoek"), ("POST", "/leden/import-mislukt")]
    assert api.aanroepen[1][3] == {"reden": reden}
    koppeling.ronde(OCHTEND + timedelta(minutes=59))
    assert paden(api)[2:] == [("GET", "/leden/importverzoek")]
    koppeling.ronde(OCHTEND + timedelta(minutes=60))
    assert paden(api)[3:] == [("GET", "/leden/importverzoek"), ("POST", "/leden/import-mislukt")]


def test_verzoek_van_een_beheerder_wacht_het_uur_na_een_fout_niet_af(api, koppeling, tmp_path):
    """BLB-006 criterium 5, besluit 2026-10-31 (#28): de bron is hersteld, de beheerder vraagt."""
    koppeling.cfg["bron"] = bronnen.StubBron(str(tmp_path / "ontbreekt.json"))
    koppeling.ronde(OCHTEND)
    koppeling.cfg["bron"] = bronnen.StubBron(str(FIXTURE))
    api.verzoek = True
    koppeling.ronde(OCHTEND + timedelta(minutes=1))
    assert paden(api)[-1] == ("PUT", "/leden")


@pytest.mark.parametrize("pad,status", [("/leden/importverzoek", 401), ("/leden/importverzoek", 403),
                                        ("/leden/importverzoek", 429), ("/leden", 422),
                                        ("/leden", 500)],
                         ids=["401", "403", "429", "put-422", "put-500"])
def test_fout_van_de_api_een_uur_stil_ook_bij_een_verzoek_behalve_met_een_nieuw_token(
        api, koppeling, pad, status):
    """BLB-039 criterium 3 en #28: het verzoek blijft open, dus geen aanroep per minuut."""
    api.status[pad], api.verzoek = status, True
    koppeling.ronde(OCHTEND)
    eerst = len(api.aanroepen)
    koppeling.ronde(OCHTEND + timedelta(minutes=1))
    assert len(api.aanroepen) == eerst
    nieuw = "blb_" + "B" * 60
    koppeling.token.write_text(nieuw)
    del api.status[pad]
    koppeling.ronde(OCHTEND + timedelta(minutes=2))
    assert [a for _m, _p, a, _l in api.aanroepen[eerst:]] == [f"Bearer {nieuw}"] * 2


def test_onverwachte_fout_ook_een_uur_stil(api, koppeling):
    """De lus draait door; het verzoek blijft open, dus geen poging per minuut (#28)."""
    class Kapot:
        def haal_leden(self):
            raise RuntimeError
    koppeling.cfg["bron"], api.verzoek = Kapot(), True
    koppeling.ronde(OCHTEND)
    koppeling.ronde(OCHTEND + timedelta(minutes=1))
    assert paden(api) == [("GET", "/leden/importverzoek")]


def test_veiligheidsgrens_van_de_api_telt_als_fout(api, koppeling, caplog):
    """BLB-007 criterium 4: de API houdt een halve lijst tegen (409); de container wacht."""
    api.status["/leden"], api.fout = 409, "De lijst bevat minder dan de helft van de leden."
    koppeling.ronde(OCHTEND)
    assert koppeling.geslaagd_op is None and koppeling.fout_op == OCHTEND
    koppeling.ronde(OCHTEND + timedelta(minutes=30))
    assert paden(api)[2:] == [("GET", "/leden/importverzoek")]
    api.verzoek = True  # #31: het verzoek van een beheerder gaat na de veiligheidsgrens direct
    koppeling.ronde(OCHTEND + timedelta(minutes=31))
    assert paden(api)[3:] == [("GET", "/leden/importverzoek"), ("PUT", "/leden")]
    assert "of direct na een verzoek van een beheerder" in caplog.text


def test_lopende_import_een_uur_stil_ook_bij_een_open_verzoek(api, koppeling, caplog):
    """#31: een vastgehouden importslot sluit het verzoek niet; geen PUT per minuut."""
    api.status["/leden"], api.fout, api.verzoek = 409, "Er loopt al een import.", True
    koppeling.ronde(OCHTEND)
    koppeling.ronde(OCHTEND + timedelta(minutes=59))
    assert paden(api) == [("GET", "/leden/importverzoek"), ("PUT", "/leden")]
    koppeling.ronde(OCHTEND + timedelta(minutes=60))
    assert paden(api)[2:] == [("GET", "/leden/importverzoek"), ("PUT", "/leden")]
    assert "HTTP 409 importslot" in caplog.text and "beheerder" not in caplog.text


@pytest.mark.parametrize("status,melding", [(200, "antwoord te groot"), (409, "HTTP 409)")])
def test_te_groot_antwoord_leest_hooguit_de_grens_en_telt_als_fout(api, koppeling, caplog,
                                                                    status, melding):
    """#109: de container wacht niet op het einde van het antwoord; de ronde eindigt met een fout."""
    api.status["/leden/importverzoek"], api.groot = status, True
    koppeling.ronde(OCHTEND)
    assert not api.klaar  # de nep-API houdt de verbinding nog open
    assert koppeling.fout_op == OCHTEND and f"Import mislukt ({melding}" in caplog.text


@pytest.mark.parametrize("status", [301, 302, 307, 308])
def test_redirect_faalt_zonder_het_token_naar_het_nieuwe_adres(api, koppeling, status):
    """#23: de container volgt geen redirect, dus het token gaat niet naar een ander adres."""
    elders = NepApi()
    try:
        api.status["/leden/importverzoek"], api.locatie = status, elders.url + "/leden/importverzoek"
        with pytest.raises(ApiFout, match=f"HTTP {status}"):
            koppeling.roep(TOKEN, "GET", "/leden/importverzoek")
        assert paden(api) == [("GET", "/leden/importverzoek")] and elders.aanroepen == []
    finally:
        elders.shutdown()
        elders.server_close()


def test_zonder_token_melden_en_niets_aanroepen(api, koppeling, caplog):
    """BLB-039 criterium 4: de lus probeert het een minuut later opnieuw (RONDE)."""
    koppeling.token.write_text("\n")
    koppeling.ronde(OCHTEND)
    koppeling.token.unlink()
    koppeling.ronde(OCHTEND)
    assert api.aanroepen == [] and caplog.text.count("Geen token") == 2
    assert "RONDE = 60" in (ROOT / "integratie/koppeling/__main__.py").read_text()


def test_te_grote_lijst_gemeld_als_onleesbaar_zonder_put(api, koppeling, tmp_path):
    """Boven de grenzen van de API (BLB-007 criterium 3) stuurt de container niets."""
    bron = tmp_path / "leden.json"
    bron.write_text(json.dumps([{"lidnummer": str(n), "naam": "x" * 500} for n in range(4500)]))
    assert len(bron.read_bytes()) > MAX_BYTES
    koppeling.cfg["bron"] = bronnen.StubBron(str(bron))
    koppeling.ronde(OCHTEND)
    assert paden(api) == [("GET", "/leden/importverzoek"), ("POST", "/leden/import-mislukt")]
    assert api.aanroepen[1][3] == {"reden": "bron_onleesbaar"}


INLOG = {"EBOEKHOUDEN_USERNAME": "gebruiker-x", "EBOEKHOUDEN_CODE1": "code1-x",
         "EBOEKHOUDEN_CODE2": "code2-x"}
EB = {"LEDENBRON": "eboekhouden", **INLOG}


@pytest.mark.parametrize("omgeving,melding", [
    ({"SYNC_TIJDSTIP": "drie uur"}, "SYNC_TIJDSTIP"),
    ({"LEDENBRON": "onbekend"}, "LEDENBRON"),
    ({"LEDENBRON": "eboekhouden"}, "EBOEKHOUDEN_USERNAME"),
    ({**EB, "EBOEKHOUDEN_USERNAME": ""}, "EBOEKHOUDEN_USERNAME"),
    ({**EB, "EBOEKHOUDEN_CODE1": "  "}, "EBOEKHOUDEN_CODE1"),
    ({k: v for k, v in EB.items() if k != "EBOEKHOUDEN_CODE2"}, "EBOEKHOUDEN_CODE2"),
    ({**EB, "BOOTAANTALLEN_SCHRIJVEN": "ja"}, "BOOTAANTALLEN_SCHRIJVEN moet aan of uit"),
    ({**EB, "BOOTAANTALLEN_SCHRIJVEN": ""}, "BOOTAANTALLEN_SCHRIJVEN moet aan of uit"),
    ({"BOOTAANTALLEN_SCHRIJVEN": "aan"}, "LEDENBRON=eboekhouden"),
    ({"LEDENBRON": "stub", "BOOTAANTALLEN_SCHRIJVEN": "aan"}, "LEDENBRON=eboekhouden"),
])
def test_ongeldige_instelling(omgeving, melding):
    with pytest.raises(ValueError, match=melding) as fout:
        instellingen(omgeving)
    for waarde in INLOG.values():  # de melding noemt de variabelen, nooit de waarden
        assert waarde not in str(fout.value)


@pytest.mark.parametrize("schakelaar,verwacht", [(None, False), ("uit", False), ("aan", True),
                                                 (" AAN ", True)])
def test_eboekhouden_met_inloggegevens_en_de_schakelaar_voor_terugschrijven(schakelaar, verwacht):
    omgeving = EB | ({} if schakelaar is None else {"BOOTAANTALLEN_SCHRIJVEN": schakelaar})
    cfg = instellingen(omgeving)
    assert type(cfg["bron"]).__name__ == "EboekhoudenBron" and cfg["bron"].kan_terugschrijven
    assert cfg["schrijven"] is verwacht


def test_instellingen_uit_de_omgeving_met_standaarden():
    cfg = instellingen({})
    assert (cfg["api_url"], cfg["token_bestand"], str(cfg["tijdstip"]), cfg["bron"]) == (
        "http://traefik:8081/api/v1", "/run/secrets/api_token", "03:00:00", None)
    cfg = instellingen({"API_URL": "http://x/api/v1/", "SYNC_TIJDSTIP": "05:30", "TZ": "UTC",
                        "LEDENBRON": "stub", "LEDENBRON_STUB_BESTAND": "/data/x.json"})
    assert (cfg["api_url"], str(cfg["tijdstip"]), str(cfg["tz"]), cfg["bron"].pad) == (
        "http://x/api/v1", "05:30:00", "UTC", "/data/x.json")


def test_stub_kan_niet_terugschrijven():
    """BLB-009 criterium 1: de stub schrijft nergens heen."""
    bron = bronnen.StubBron("x")
    assert not bron.kan_terugschrijven
    with pytest.raises(bronnen.NietBeschikbaar):
        bron.schrijf_bootaantallen([])


class SchrijfBron:
    """Een bron die kan terugschrijven en vastlegt wat hij kreeg (de SOAP-kant staat in
    tests/integratie)."""

    kan_terugschrijven = True

    def __init__(self, fout=None):
        self.ontvangen, self.fout = [], fout

    def haal_leden(self):
        return json.loads(FIXTURE.read_text())

    def schrijf_bootaantallen(self, aantallen):
        self.ontvangen.append(aantallen)
        if self.fout:
            raise self.fout
        return {"geschreven": 1, "ongewijzigd": 2, "niet_gevonden": 3, "fout": 4}


def met_bron(koppeling, bron, schrijven=True):
    koppeling.cfg["bron"], koppeling.cfg["schrijven"] = bron, schrijven
    return bron


def test_na_een_geslaagde_import_gaan_de_bootaantallen_naar_de_bron(api, koppeling, caplog):
    """#178 besluit 4: alleen met de schakelaar aan, na de import, en één logregel met getallen."""
    bron = met_bron(koppeling, SchrijfBron())
    api.verzoek = True
    with caplog.at_level(logging.INFO):
        koppeling.ronde(OCHTEND)
    assert paden(api) == [("GET", "/leden/importverzoek"), ("PUT", "/leden"),
                          ("GET", "/bootaantallen")]
    assert bron.ontvangen == [api.bootaantallen]  # ongewijzigd doorgegeven
    regel = [r for r in caplog.messages if r.startswith("Terugschrijven")]
    assert regel == [
        "Terugschrijven: {'geschreven': 1, 'ongewijzigd': 2, 'niet_gevonden': 3, 'fout': 4}"]
    for sleutel in ("code", "adres", "telefoon", "email", "lidnummer", "Kajak"):
        assert sleutel not in regel[0]


def test_schakelaar_uit_schrijft_niets_en_vraagt_niets_op(api, koppeling):
    bron = met_bron(koppeling, SchrijfBron(), schrijven=False)
    api.verzoek = True
    koppeling.ronde(OCHTEND)
    assert paden(api) == [("GET", "/leden/importverzoek"), ("PUT", "/leden")]
    assert bron.ontvangen == []


def test_mislukte_import_schrijft_niet_terug(api, koppeling):
    bron = met_bron(koppeling, SchrijfBron())
    api.verzoek, api.status["/leden"] = True, 500
    koppeling.ronde(OCHTEND)
    assert ("GET", "/bootaantallen") not in paden(api) and bron.ontvangen == []


@pytest.mark.parametrize("opstelling,melding", [
    ("api", "Terugschrijven mislukt (HTTP 500)."),
    (bronnen.LedenbronFout("bron_geweigerd"), "Terugschrijven mislukt (bron_geweigerd)."),
    (RuntimeError("geheime tekst"), "Terugschrijven mislukt (RuntimeError)."),
], ids=["api", "bron", "onverwacht"])
def test_fout_bij_terugschrijven_maakt_de_import_niet_mislukt_en_wordt_niet_herhaald(
        api, koppeling, caplog, opstelling, melding):
    bron = met_bron(koppeling, SchrijfBron(None if opstelling == "api" else opstelling))
    if opstelling == "api":
        api.status["/bootaantallen"] = 500
    api.verzoek = True
    with caplog.at_level(logging.INFO):
        koppeling.ronde(OCHTEND)
    assert melding in caplog.messages and "geheime tekst" not in caplog.text
    assert koppeling.geslaagd_op == OCHTEND.date() and koppeling.fout_op is None
    assert "POST" not in [m for m, _ in paden(api)]  # geen import-mislukt
    api.verzoek = False
    koppeling.ronde(OCHTEND + timedelta(minutes=1))  # geen extra herhaling
    assert paden(api)[-1] == ("GET", "/leden/importverzoek")
    assert len(bron.ontvangen) == (0 if opstelling == "api" else 1)


def lus(api, tmp_path, **omgeving):
    """Start python -m koppeling zoals de container en stopt hem na 3 seconden met SIGTERM."""
    proces = subprocess.Popen(
        [sys.executable, "-m", "koppeling"], cwd=ROOT / "integratie", text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env={"PATH": os.environ["PATH"], "API_URL": api.url,
             "API_TOKEN_FILE": str(tmp_path / "api_token"), **omgeving})
    try:
        proces.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proces.terminate()
    return proces.wait(timeout=5), proces.stdout.read()


def test_zonder_bron_meldt_de_container_dat_en_roept_de_api_niet_aan(api, tmp_path):
    """BLB-007 criterium 2. SIGTERM stopt de container meteen, ook als PID 1."""
    (tmp_path / "api_token").write_text(TOKEN)
    code, log = lus(api, tmp_path, LEDENBRON="")
    assert code == 0 and "Geen ledenbron ingesteld" in log and api.aanroepen == []


def test_de_lus_importeert_bij_het_starten(api, tmp_path):
    (tmp_path / "api_token").write_text(TOKEN)
    code, log = lus(api, tmp_path, LEDENBRON="stub", LEDENBRON_STUB_BESTAND=str(FIXTURE),
                    SYNC_TIJDSTIP="00:00")
    assert code == 0 and "Import geslaagd" in log and TOKEN not in log
    assert paden(api) == [("GET", "/leden/importverzoek"), ("PUT", "/leden")]


def test_ongeldige_instelling_stopt_de_container(api, tmp_path):
    code, log = lus(api, tmp_path, LEDENBRON="eboekhouden")
    assert code == 1 and "LEDENBRON" in log


def _top_imports(bestand):
    """De modules die bovenaan het bestand geïmporteerd worden (niet in een functie)."""
    for knoop in ast.parse(bestand.read_text()).body:
        yield from ([a.name for a in knoop.names] if isinstance(knoop, ast.Import) else (
            [knoop.module] if isinstance(knoop, ast.ImportFrom) else []))


def test_container_gebruikt_buiten_de_bron_alleen_de_standaardbibliotheek():
    """ADR-012 v1.8.0: alleen koppeling/eboekhouden.py gebruikt zeep en requests, en laadt ze pas
    bij gebruik, dus niet bij het starten met de stub of zonder bron."""
    for bestand in (ROOT / "integratie/koppeling").glob("*.py"):
        for naam in _top_imports(bestand):
            top = naam.split(".")[0]
            assert top == "koppeling" or top in sys.stdlib_module_names, (bestand, naam)
    assert not [n for b in (ROOT / "integratie/koppeling").glob("*.py") if b.name != "eboekhouden.py"
                for n in ast.walk(ast.parse(b.read_text()))
                if isinstance(n, ast.Import | ast.ImportFrom)
                and getattr(n, "module", None) in ("zeep", "requests")]


def test_zeep_alleen_in_het_image_van_de_integratie():
    """#178 besluit 6: geen zeep en geen e-boekhoudencode in het applicatie-image."""
    for pad in ("pyproject.toml", "uv.lock", "docker/Dockerfile"):
        assert "zeep" not in (ROOT / pad).read_text().lower(), pad
    for bestand in (ROOT / "app").rglob("*.py"):
        tekst = bestand.read_text().lower()
        assert "zeep" not in tekst and "import eboekhouden" not in tekst, bestand


def test_afhankelijkheden_van_de_integratie_zijn_vastgepind_met_hashes():
    """Elk pakket in requirements*.txt staat op een versie met een hash voor elk bestand."""
    for naam in ("requirements.txt", "requirements-test.txt"):
        blokken = re.split(r"\n(?=\S)", (ROOT / "integratie" / naam).read_text().strip())
        assert blokken
        for blok in blokken:
            assert re.match(r"[\w.-]+==[\w.]+ \\\n", blok), blok
            assert len(re.findall(r"--hash=sha256:[0-9a-f]{64}", blok)) >= 1, blok
    assert "zeep" in (ROOT / "integratie/requirements.txt").read_text()


def test_image_van_de_integratie_zonder_pip_en_zonder_root():
    dockerfile = (ROOT / "integratie/Dockerfile").read_text()
    eind = dockerfile.split("\nFROM ")[-1]
    assert "pip install" not in eind and "pip uninstall" in eind
    assert "COPY --from=bouw /pakketten /pakketten" in eind and "USER 10001" in eind
    assert "--require-hashes" in dockerfile.split("\nFROM ")[1]
    assert "app" not in eind.split("COPY koppeling")[0].split("COPY --from=bouw")[0]


def test_dependabot_volgt_de_afhankelijkheden_van_de_integratie():
    regels = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text())["updates"]
    assert [r for r in regels if r["package-ecosystem"] == "pip" and r["directory"] == "/integratie"]


# docker-compose.yml (ADR-012)

COMPOSE = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
DIENSTEN = COMPOSE["services"]


def test_integratie_alleen_op_koppeling_en_buiten():
    """BLB-039 criterium 1: de container bereikt db en api niet rechtstreeks. Op koppeling staat
    verder alleen de gedeelde Traefik, buiten deze compose (ADR-013)."""
    assert set(DIENSTEN["integratie"]["networks"]) == {"koppeling", "buiten"}
    op_koppeling = {n for n, d in DIENSTEN.items() if "koppeling" in d.get("networks", [])}
    assert op_koppeling == {"integratie"}
    assert COMPOSE["networks"]["koppeling"]["external"] is True
    assert DIENSTEN["integratie"]["environment"]["API_URL"] == (
        "${API_URL:-http://traefik:8081/api/v1}")


def test_web_en_api_alleen_op_de_netwerken_van_de_installatie():
    """ADR-013: web en api niet op het gedeelde netwerk van Traefik; api heeft geen router op
    websecure of web, alleen op intern vanaf KOPPELNET. Geen eigen proxy in deze compose."""
    assert not {"nginx", "traefik"} & set(DIENSTEN)
    for naam in ("web", "api"):
        assert set(DIENSTEN[naam]["networks"]) == {"achterkant", "voorkant"}
    assert COMPOSE["networks"]["voorkant"] == {
        "name": "${INSTALLATIE:-botenloods}_voorkant", "external": True}
    labels = dict(regel.split("=", 1) for regel in DIENSTEN["api"]["labels"])
    entrypoints = {v for k, v in labels.items() if k.endswith(".entrypoints")}
    assert entrypoints == {"intern"}
    assert labels["traefik.http.routers.${INSTALLATIE:-botenloods}-api.rule"].startswith(
        "ClientIP(`${KOPPELNET:-10.203.0.0/24}`) && ")


def test_elke_router_zonder_toegangslog_van_traefik():
    """ADR-013, #5, #14: de toegangslog staat in web en api, niet in de gedeelde Traefik."""
    for naam in ("web", "api"):
        labels = dict(regel.split("=", 1) for regel in DIENSTEN[naam]["labels"])
        routers = {k.split(".")[3] for k in labels if k.startswith("traefik.http.routers.")}
        assert routers
        for router in routers:
            sleutel = f"traefik.http.routers.{router}.observability.accesslogs"
            assert labels[sleutel] == "false", sleutel
            assert f"traefik.http.routers.{router}.entrypoints" in labels


def test_inloggegevens_en_schakelaar_alleen_in_de_omgeving_van_integratie():
    """#178 besluit 5: de drie waarden komen uit .env en staan in geen andere dienst; zonder
    waarde start de container niet (de controle staat in instellingen)."""
    omgeving = DIENSTEN["integratie"]["environment"]
    for naam in ("EBOEKHOUDEN_USERNAME", "EBOEKHOUDEN_CODE1", "EBOEKHOUDEN_CODE2"):
        assert omgeving[naam] == f"${{{naam}:-}}"
        assert f"{naam}=" in (ROOT / ".env.example").read_text()
    assert omgeving["BOOTAANTALLEN_SCHRIJVEN"] == "${BOOTAANTALLEN_SCHRIJVEN:-uit}"
    assert "BOOTAANTALLEN_SCHRIJVEN=uit" in (ROOT / ".env.example").read_text()
    for naam, dienst in DIENSTEN.items():
        if naam != "integratie":
            assert not [k for k in dienst.get("environment", {}) if k.startswith(
                ("EBOEKHOUDEN", "BOOTAANTALLEN"))], naam


def test_integratie_zonder_root_en_alleen_lezen():
    """BLB-039 criterium 6; de uid staat in het Dockerfile (vorige test)."""
    integratie = DIENSTEN["integratie"]
    assert integratie["read_only"] is True and integratie["cap_drop"] == ["ALL"]
    assert integratie["security_opt"] == ["no-new-privileges:true"]
    assert integratie["build"] == "integratie" and integratie["secrets"] == ["api_token"]
    assert COMPOSE["secrets"]["api_token"] == {"file": "./secrets/api_token"}


def test_applicatie_kent_de_bron_niet():
    """BLB-007 criterium 5, BLB-039 criterium 2: geen bron of inloggegevens in web, api of worker."""
    from app import config

    for naam in ("web", "api", "worker", "migrate"):
        omgeving = DIENSTEN[naam].get("environment", {})
        assert not [k for k in omgeving if k.startswith(("LEDENBRON", "SYNC", "EBOEKHOUDEN"))]
    assert not (ROOT / "app/ledenbron").exists()
    assert not [k for k in config.laad() if "LEDENBRON" in k or "SYNC" in k]


def test_api_van_buiten_alleen_met_compose_api_extern():
    """BLB-042, ADR-013 v1.2.0: alleen labels op api; een router op websecure met de whitelist
    van de installatie vóór de rate limits van intern; zonder API_EXTERN_BRONNEN start compose
    niet (de proef met een losse Traefik toont de werking)."""
    extern = yaml.safe_load((ROOT / "compose.api-extern.yml").read_text())
    assert set(extern) == {"services"} and set(extern["services"]) == {"api"}
    assert set(extern["services"]["api"]) == {"labels"}
    labels = dict(regel.split("=", 1) for regel in extern["services"]["api"]["labels"])
    i, router = "${INSTALLATIE:-botenloods}", "traefik.http.routers.${INSTALLATIE:-botenloods}-api-extern"
    assert labels[f"{router}.entrypoints"] == "websecure"
    assert labels[f"{router}.rule"] == "Host(`${DOMEIN}`) && PathPrefix(`/api/v1/`)"
    assert labels[f"{router}.priority"] == "2000" and labels[f"{router}.tls"] == "true"
    assert labels[f"{router}.observability.accesslogs"] == "false"
    assert labels[f"{router}.middlewares"].split(",") == [
        f"{i}-nosniff", f"{i}-externtoegang", f"{i}-tokenrem", f"{i}-iprem", f"{i}-3mb"]
    bronnen = labels[f"traefik.http.middlewares.{i}-externtoegang.ipallowlist.sourcerange"]
    assert bronnen.startswith("${API_EXTERN_BRONNEN:?")
    assert not [k for k in labels if "ipstrategy" in k.lower()]  # het verbindingsadres telt
