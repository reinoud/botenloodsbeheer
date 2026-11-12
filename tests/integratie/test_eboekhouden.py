"""Bron e-boekhouden (ADR-004, ADR-012, issue #178) tegen een nagebootste SOAP-server.

Deze tests draaien in het testdoel van integratie/Dockerfile, want alleen daar staat zeep (niet in
het applicatie-image). De server beantwoordt de echte WSDL en legt elk verzoek vast, zodat te zien
is wat zeep naar e-boekhouden stuurt. Geen enkele aanroep gaat naar e-boekhouden zelf.
Starten: docker compose -f docker-compose.yml -f compose.dev.yml run --rm --no-deps test-integratie
"""

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from xml.sax.saxutils import escape

import pytest
from koppeling import bronnen, eboekhouden
from koppeling.eboekhouden import EboekhoudenBron
from lxml import etree

NS = "http://www.e-boekhouden.nl/soap"
GEHEIM = "GEHEIME-TEKST-VAN-EBOEKHOUDEN"
INLOG = ("gebruiker-x", "code1-x", "code2-x")
WSDL = etree.parse(str(eboekhouden.WSDL))
# De volgorde van de velden in cRelatie zoals de WSDL ze voorschrijft.
VELDEN = [e.get("name") for e in WSDL.iterfind(
    ".//{*}complexType[@name='cRelatie']/{*}sequence/{*}element")]
LID = {"ID": "11", "AddDatum": "2020-01-15T00:00:00", "Code": "1001", "Bedrijf": "Jan de Vries",
       "Contactpersoon": "J. de Vries", "Adres": "Kanoweg 1", "Postcode": "1234AB",
       "Plaats": "Zwolle", "Telefoon": "0612345678", "Email": "jan@example.org",
       "Notitie": "niet aanraken", "Bankrekening": "123456789", "Girorekening": "987",
       "IBAN": "NL00TEST0123456789", "BP": "P", "Def1": "x", "Def2": "actief_gewoon",
       "Def3": "2015-03-01", "Def7": "", "Def10": "", "LA": "ja", "Gb_ID": "5", "GeenEmail": "0",
       "NieuwsbriefgroepenCount": "2"}


def relatie(**velden):
    return {**LID, **velden}


class Nep(ThreadingHTTPServer):
    """Antwoordt per SOAPAction en legt de verzoeken vast als (actie, {veld: tekst})."""

    def __init__(self):
        super().__init__(("127.0.0.1", 0), Handler)
        self.verzoeken, self.relaties = [], []
        self.login_fout = self.relaties_fout = self.update_fout = False
        self.status = self.lichaam = None  # een vaste HTTP-status of een vast antwoord
        threading.Thread(target=self.serve_forever, daemon=True).start()

    @property
    def url(self):
        return f"http://127.0.0.1:{self.server_address[1]}/soap.asmx"

    def acties(self):
        return [a for a, _ in self.verzoeken]


def _cerror(code):
    return (f"<LastErrorCode>{code}</LastErrorCode>"
            f"<LastErrorDescription>{GEHEIM}</LastErrorDescription>") if code else ""


def _fout(code):
    return f"<ErrorMsg>{_cerror(code)}</ErrorMsg>" if code else ""


def _relatie_xml(r):
    return "".join(f"<{v}>{escape(r[v])}</{v}>" for v in VELDEN if v in r)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        nep = self.server
        actie = self.headers["SOAPAction"].strip('"').rsplit("/", 1)[1]
        wortel = etree.fromstring(self.rfile.read(int(self.headers["Content-Length"])))
        invoer = wortel.find(f".//{{{NS}}}{actie}")
        nep.verzoeken.append((actie, {
            etree.QName(k).localname: (
                {etree.QName(x).localname: x.text or "" for x in k} if len(k) else k.text)
            for k in invoer}))
        binnen = {
            "OpenSession": f"<OpenSessionResult>{_fout(nep.login_fout)}<SessionID>SESS1</SessionID>"
                           "</OpenSessionResult>",
            "GetRelaties": "<GetRelatiesResult>" + _fout(nep.relaties_fout) + "<Relaties>" + "".join(
                f"<cRelatie>{_relatie_xml(r)}</cRelatie>" for r in nep.relaties)
                           + "</Relaties></GetRelatiesResult>",
            "UpdateRelatie": f"<UpdateRelatieResult>{_cerror(nep.update_fout)}</UpdateRelatieResult>",
            "CloseSession": "",
        }[actie]
        tekst = nep.lichaam or (
            '<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap='
            '"http://schemas.xmlsoap.org/soap/envelope/"><soap:Body>'
            f'<{actie}Response xmlns="{NS}">{binnen}</{actie}Response></soap:Body></soap:Envelope>')
        data = tekst.encode()
        self.send_response(nep.status or 200)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@pytest.fixture
def nep():
    server = Nep()
    yield server
    server.shutdown()
    server.server_close()


@pytest.fixture
def bron(nep):
    return EboekhoudenBron(*INLOG, adres=nep.url)


def bijwerkingen(nep):
    return [v for a, v in nep.verzoeken if a == "UpdateRelatie"]


# ophalen

def test_alleen_leden_met_de_vier_velden(nep, bron):
    """Besluit 1: Def2 die begint met actief, of met opgezegd en een opzegdatum, is lid (#221); naam is
    Bedrijf; geen adres, telefoon, e-mail."""
    nep.relaties = [
        relatie(),
        relatie(ID="12", Code="1002", Bedrijf="Piet", Def2="opgezegd", Def3="2010-01-01",
                Def7="2025-12-31"),
        relatie(ID="13", Code="2001", Bedrijf="Leverancier", Def2="crediteur"),
        relatie(ID="14", Code="2002", Bedrijf="Zonder soort", Def2=""),
        relatie(ID="16", Code="2003", Bedrijf="Oud", Def2="inactief"),  # bevat "actief"
        relatie(ID="15", Code="1003", Bedrijf="Kees", Def2="actief_jeugd", Def3="", Def7=""),
        relatie(ID="17", Code="1004", Bedrijf="Opgezegd zonder datum", Def2="opgezegd", Def7=" "),  # #221
        relatie(ID="18", Code="1005", Bedrijf="Opgezegd, lege datum", Def2="opgezegd_gewoon", Def7=""),
        relatie(ID="19", Code="1006", Bedrijf="Hoofdletter", Def2=" Actief_gewoon", Def3="", Def7=""),  # #226
        relatie(ID="20", Code="1007", Bedrijf="Opgezegd, hoofdletter", Def2="Opgezegd_gewoon ",
                Def7=""),  # #226
    ]
    assert bron.haal_leden() == [
        {"lidnummer": "1001", "naam": "Jan de Vries", "lid_sinds": "2015-03-01", "opzegdatum": None},
        {"lidnummer": "1002", "naam": "Piet", "lid_sinds": "2010-01-01", "opzegdatum": "2025-12-31"},
        {"lidnummer": "1003", "naam": "Kees", "lid_sinds": None, "opzegdatum": None},
        {"lidnummer": "1006", "naam": "Hoofdletter", "lid_sinds": None, "opzegdatum": None},
    ]


def test_geen_relaties_geeft_een_lege_lijst(nep, bron):
    assert bron.haal_leden() == []


def test_inloggen_met_de_drie_codes_en_de_sessie_daarna_sluiten(nep, bron):
    nep.relaties = [relatie()]
    bron.haal_leden()
    assert nep.acties() == ["OpenSession", "GetRelaties", "CloseSession"]
    open_, relaties, sluit = (v for _, v in nep.verzoeken)
    assert (open_["Username"], open_["SecurityCode1"], open_["SecurityCode2"]) == INLOG
    assert (relaties["SessionID"], relaties["SecurityCode2"]) == ("SESS1", INLOG[2])
    assert sluit == {"SessionID": "SESS1"}


def test_het_adres_van_de_dienst_is_https():
    """De WSDL noemt http; zonder eigen adres gingen de inloggegevens onversleuteld over de lijn."""
    assert "location=\"http://" in Path(eboekhouden.WSDL).read_text()
    assert EboekhoudenBron(*INLOG)._adres == "https://soap.e-boekhouden.nl/soap.asmx"
    assert bronnen.kies({"LEDENBRON": "eboekhouden", **dict(zip(bronnen.EBOEKHOUDEN_INLOG, INLOG))}
                        )._adres.startswith("https://")


def test_zeep_schrijft_niets_naar_schijf(bron):
    """De container is alleen-lezen: geen cache van de WSDL."""
    bron._service = bron._verbind()
    assert bron._service._client.transport.cache is None


# terugschrijven

AANTALLEN = [{"lidnummer": "1001", "aantallen": {"Kajak": 1, "Canadese kano": 2, "Surfski é": 0}}]
DEF10 = '{"Kajak": 1, "Canadese kano": 2, "Surfski é": 0}'


def test_schrijven_wijzigt_alleen_def10_en_stuurt_de_rest_ongewijzigd_terug(nep, bron):
    """Besluit 2: het volledige record, ook velden zonder model, gaat terug op Def10 na."""
    nep.relaties = [relatie()]
    uitkomst = bron.schrijf_bootaantallen(AANTALLEN)
    assert uitkomst == {"geschreven": 1, "ongewijzigd": 0, "niet_gevonden": 0, "fout": 0}
    assert nep.acties() == ["OpenSession", "GetRelaties", "UpdateRelatie", "CloseSession"]
    [verzoek] = bijwerkingen(nep)
    assert (verzoek["SessionID"], verzoek["SecurityCode2"]) == ("SESS1", INLOG[2])
    verstuurd = verzoek["oRel"]
    assert verstuurd.pop("Def10") == DEF10
    verwacht = {k: v for k, v in relatie().items() if k != "Def10" and v != ""}
    assert {k: v for k, v in verstuurd.items() if v != ""} == verwacht
    assert "Bankrekening" in verstuurd and "Girorekening" in verstuurd


def test_gelijke_waarde_wordt_niet_geschreven(nep, bron):
    nep.relaties = [relatie(Def10=DEF10)]
    assert bron.schrijf_bootaantallen(AANTALLEN) == {
        "geschreven": 0, "ongewijzigd": 1, "niet_gevonden": 0, "fout": 0}
    assert bijwerkingen(nep) == []


def test_onbekend_lidnummer_en_geen_lid_worden_overgeslagen(nep, bron):
    """Een relatie die geen lid is (Def2, of opgezegd zonder Def7: #221), raakt de koppeling nooit."""
    nep.relaties = [relatie(Code="2001", Def2="crediteur"), relatie(Code="2004", Def2="opgezegd")]
    uitkomst = bron.schrijf_bootaantallen(AANTALLEN + [{"lidnummer": "2001", "aantallen": {}},
                                                      {"lidnummer": "2004", "aantallen": {}},
                                                      {"lidnummer": "9999", "aantallen": {}}])
    assert uitkomst == {"geschreven": 0, "ongewijzigd": 0, "niet_gevonden": 4, "fout": 0}
    assert bijwerkingen(nep) == []


def test_fout_bij_schrijven_telt_zonder_tekst_en_zonder_herhaling(nep, bron, caplog):
    nep.relaties = [relatie(Code=str(n)) for n in range(1, 4)]
    nep.update_fout = True
    with caplog.at_level(logging.INFO):
        uitkomst = bron.schrijf_bootaantallen(
            [{"lidnummer": str(n), "aantallen": {"Kajak": n}} for n in range(1, 4)])
    assert uitkomst == {"geschreven": 0, "ongewijzigd": 0, "niet_gevonden": 0, "fout": 3}
    assert len(bijwerkingen(nep)) == 3  # elk lid één poging
    assert GEHEIM not in caplog.text
    assert nep.acties()[-1] == "CloseSession"


def test_na_drie_fouten_achter_elkaar_stopt_het_schrijven(nep, bron):
    nep.relaties = [relatie(Code=str(n)) for n in range(1, 8)]
    nep.update_fout = True
    uitkomst = bron.schrijf_bootaantallen(
        [{"lidnummer": str(n), "aantallen": {"Kajak": n}} for n in range(1, 8)])
    assert uitkomst["fout"] == 7 and len(bijwerkingen(nep)) == 3


def test_fouten_met_een_geslaagd_lid_ertussen_zijn_niet_achter_elkaar(nep, bron):
    """Fout, ongewijzigd, fout, ...: de teller begint na elk geslaagd lid opnieuw (#178)."""
    nep.relaties = [relatie(Code=str(n), Def10=json.dumps({"Kajak": n}) if n % 2 == 0 else "")
                    for n in range(1, 8)]
    nep.update_fout = True
    uitkomst = bron.schrijf_bootaantallen(
        [{"lidnummer": str(n), "aantallen": {"Kajak": n}} for n in range(1, 8)])
    assert uitkomst == {"geschreven": 0, "ongewijzigd": 3, "niet_gevonden": 0, "fout": 4}
    assert len(bijwerkingen(nep)) == 4


# fouten van de bron

def verbroken(nep):
    nep.server_close()
    nep.shutdown()


@pytest.mark.parametrize("opstelling,reden", [
    (lambda n: setattr(n, "login_fout", "42"), "bron_geweigerd"),
    (lambda n: setattr(n, "relaties_fout", "17"), "bron_geweigerd"),
    (lambda n: (setattr(n, "status", 401), setattr(n, "lichaam", "Nee " + GEHEIM)), "bron_geweigerd"),
    (lambda n: (setattr(n, "status", 403), setattr(n, "lichaam", "Nee " + GEHEIM)), "bron_geweigerd"),
    (lambda n: (setattr(n, "status", 502), setattr(n, "lichaam", "Nee " + GEHEIM)), "bron_onbereikbaar"),
    (lambda n: setattr(n, "lichaam", "dit is geen xml " + GEHEIM), "bron_onleesbaar"),
    (lambda n: setattr(n, "lichaam", f'<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/'
                       f'envelope/"><soap:Body><soap:Fault><faultcode>soap:Server</faultcode>'
                       f'<faultstring>{GEHEIM}</faultstring></soap:Fault></soap:Body>'
                       f'</soap:Envelope>'), "bron_onleesbaar"),
    (verbroken, "bron_onbereikbaar"),
], ids=["login-geweigerd", "relaties-geweigerd", "401", "403", "502", "geen-xml", "soapfault",
        "verbinding-weg"])
def test_elke_foutsoort_wordt_een_reden_uit_de_vaste_lijst(nep, bron, caplog, opstelling, reden):
    """Geen tekst van e-boekhouden in de fout of het log."""
    opstelling(nep)
    for aanroep in (bron.haal_leden, lambda: bron.schrijf_bootaantallen(AANTALLEN)):
        with caplog.at_level(logging.DEBUG), pytest.raises(bronnen.LedenbronFout) as fout:
            aanroep()
        assert str(fout.value) == reden
    assert GEHEIM not in caplog.text and GEHEIM not in repr(fout.value)
    for geheim in INLOG:
        assert geheim not in caplog.text


def test_sessie_wordt_ook_na_een_fout_gesloten(nep, bron):
    nep.relaties_fout = "17"
    with pytest.raises(bronnen.LedenbronFout):
        bron.haal_leden()
    assert nep.acties() == ["OpenSession", "GetRelaties", "CloseSession"]
