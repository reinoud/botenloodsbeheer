"""Integratiecontainer (BLB-006, 007, 039; ADR-004, ADR-012) met de stub en een nep-API, en de
opbouw van docker-compose.yml. Zonder database: de container kent alleen de API."""

import ast
import json
import logging
import os
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

from koppeling import MAX_BYTES, Koppeling, bronnen, instellingen

TZ = ZoneInfo("Europe/Amsterdam")
OCHTEND = datetime(2026, 10, 31, 10, 0, tzinfo=TZ)
TOKEN = "blb_" + "A" * 60
FIXTURE = ROOT / "tests/fixtures/leden.json"


class NepApi(ThreadingHTTPServer):
    """Legt elke aanroep vast en antwoordt met een vaste status per pad."""

    def __init__(self):
        super().__init__(("127.0.0.1", 0), Handler)
        self.aanroepen, self.verzoek, self.status = [], False, {}
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
        antwoord = {"aangevraagd": self.server.verzoek} if pad == "/leden/importverzoek" else (
            {"ontvangen": len(lichaam["leden"]), "nieuw": 1} if pad == "/leden" else {})
        tekst = json.dumps(antwoord if status < 400 else {"fout": "Geen toegang."}).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(tekst)))
        self.end_headers()
        self.wfile.write(tekst)

    do_GET = do_PUT = do_POST = _antwoord


@pytest.fixture
def api():
    server = NepApi()
    yield server
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


def test_veiligheidsgrens_van_de_api_telt_als_fout(api, koppeling):
    """BLB-007 criterium 4: de API houdt een halve lijst tegen (409); de container wacht."""
    api.status["/leden"] = 409
    koppeling.ronde(OCHTEND)
    assert koppeling.geslaagd_op is None and koppeling.fout_op == OCHTEND
    koppeling.ronde(OCHTEND + timedelta(minutes=30))
    assert paden(api)[2:] == [("GET", "/leden/importverzoek")]


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


@pytest.mark.parametrize("omgeving,melding", [({"SYNC_TIJDSTIP": "drie uur"}, "SYNC_TIJDSTIP"),
                                              ({"LEDENBRON": "eboekhouden"}, "LEDENBRON")])
def test_ongeldige_instelling(omgeving, melding):
    with pytest.raises(ValueError, match=melding):
        instellingen(omgeving)


def test_instellingen_uit_de_omgeving_met_standaarden():
    cfg = instellingen({})
    assert (cfg["api_url"], cfg["token_bestand"], str(cfg["tijdstip"]), cfg["bron"]) == (
        "http://nginx:8081/api/v1", "/run/secrets/api_token", "03:00:00", None)
    cfg = instellingen({"API_URL": "http://x/api/v1/", "SYNC_TIJDSTIP": "05:30", "TZ": "UTC",
                        "LEDENBRON": "stub", "LEDENBRON_STUB_BESTAND": "/data/x.json"})
    assert (cfg["api_url"], str(cfg["tijdstip"]), str(cfg["tz"]), cfg["bron"].pad) == (
        "http://x/api/v1", "05:30:00", "UTC", "/data/x.json")


def test_terugschrijven_niet_beschikbaar():
    """BLB-009 criterium 1, deel container."""
    bron = bronnen.StubBron("x")
    assert not bron.kan_terugschrijven
    with pytest.raises(bronnen.NietBeschikbaar):
        bron.schrijf_bootaantallen({})


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


def test_container_gebruikt_alleen_de_standaardbibliotheek():
    """ADR-012: eigen image zonder applicatiecode en zonder afhankelijkheden."""
    for bestand in (ROOT / "integratie/koppeling").glob("*.py"):
        for knoop in ast.walk(ast.parse(bestand.read_text())):
            namen = [a.name for a in knoop.names] if isinstance(knoop, ast.Import) else (
                [knoop.module] if isinstance(knoop, ast.ImportFrom) else [])
            for naam in namen:
                top = naam.split(".")[0]
                assert top == "koppeling" or top in sys.stdlib_module_names, (bestand, naam)
    dockerfile = (ROOT / "integratie/Dockerfile").read_text()
    assert "COPY koppeling koppeling" in dockerfile and "app" not in dockerfile.split("COPY")[1]
    assert "USER 10001" in dockerfile


# docker-compose.yml (ADR-012)

COMPOSE = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
DIENSTEN = COMPOSE["services"]


def test_integratie_alleen_op_koppeling_en_buiten():
    """BLB-039 criterium 1: de container bereikt db en api niet rechtstreeks."""
    assert set(DIENSTEN["integratie"]["networks"]) == {"koppeling", "buiten"}
    op_koppeling = {n for n, d in DIENSTEN.items() if "koppeling" in d.get("networks", [])}
    assert op_koppeling == {"nginx", "integratie"}
    assert COMPOSE["networks"]["koppeling"]["internal"] is True
    assert DIENSTEN["integratie"]["environment"]["API_URL"] == "http://nginx:8081/api/v1"


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
