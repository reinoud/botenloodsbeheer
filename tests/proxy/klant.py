"""Client voor tests/proxy/draai.sh: draait in een container met een vast adres en roept
/api/v1/ik aan via de losse Traefik. Geeft exitcode 1 als een status afwijkt.

    klant.py <verwacht>[,<verwacht>...] [Kop: waarde | -]...   een aanroep per kop, - is zonder kop
    klant.py tempo                              12 aanroepen achter elkaar, vanaf de 11e 429

Omgeving: DOEL (adres:poort van Traefik), SCHEMA (https of http), DOMEIN (Host-kop),
TOKEN (optioneel), PAD (standaard /api/v1/ik), WACHT=1 (wacht tot Traefik de router kent).
Het token komt nergens in de uitvoer.
"""
import http.client
import json
import os
import ssl
import sys
import time

DOEL, SCHEMA, DOMEIN = os.environ["DOEL"], os.environ["SCHEMA"], os.environ["DOMEIN"]
TOKEN = os.environ.get("TOKEN")
PAD = os.environ.get("PAD") or "/api/v1/ik"
# Platte tekst die Traefik zelf geeft; elk ander antwoord komt van de applicatie of is onbekend.
TRAEFIK = {400: b"Bad Request", 403: b"Forbidden", 404: b"404 page not found\n",
           429: b"Too Many Requests"}
# Het standaardcertificaat van een losse Traefik is zelf ondertekend.
CONTEXT = ssl._create_unverified_context()


def aanroep(kop=None):
    host, poort = DOEL.split(":")
    if SCHEMA == "https":
        verbinding = http.client.HTTPSConnection(host, int(poort), timeout=10, context=CONTEXT)
    else:
        verbinding = http.client.HTTPConnection(host, int(poort), timeout=10)
    # skip_host: met een eigen Host-kop naast die van http.client geeft Traefik 400.
    verbinding.putrequest("GET", PAD, skip_host=True)
    verbinding.putheader("Host", DOMEIN)
    if TOKEN:
        verbinding.putheader("Authorization", f"Bearer {TOKEN}")
    if kop:
        naam, waarde = kop.split(":", 1)
        verbinding.putheader(naam.strip(), waarde.strip())
    verbinding.endheaders()
    antwoord = verbinding.getresponse()
    lichaam = antwoord.read()
    verbinding.close()
    return antwoord.status, antwoord, lichaam


def herkomst(code, antwoord, lichaam):
    """Wie antwoordde: de applicatie geeft JSON, Traefik zijn eigen platte tekst."""
    soort = antwoord.getheader("Content-Type") or ""
    if soort.startswith("application/json"):
        return "applicatie"
    # De 403 en 429 van Traefik hebben geen Content-Type, de 404 wel text/plain.
    if soort in ("", "text/plain; charset=utf-8") and lichaam == TRAEFIK.get(code):
        return "Traefik"
    return f"onbekend ({soort!r}, {lichaam[:30]!r})"


def status(verwacht, koppen):
    if os.environ.get("WACHT") == "1":
        # Traefik kent de router pas als api gezond is en het event verwerkt is; tot dan 404.
        for _ in range(40):
            if aanroep()[0] != 404:
                break
            time.sleep(0.5)
    goed = True
    for kop in koppen or ["-"]:
        code, antwoord, lichaam = aanroep(None if kop == "-" else kop)
        bron = herkomst(code, antwoord, lichaam)
        # 200 en 401 moeten van de applicatie komen, de rest van Traefik.
        ok = code in verwacht and bron == ("applicatie" if code in (200, 401) else "Traefik")
        if code == 200 and ok:
            ok = "token" in json.loads(lichaam)
        goed &= ok
        print(f"{'OK ' if ok else 'FOUT'} {PAD}: verwacht {verwacht}, kreeg {code} van {bron}; "
              f"kop: {'geen' if kop == '-' else kop}")
    return goed


def tempo():
    antwoorden = [aanroep() for _ in range(12)]
    codes = [code for code, _, _ in antwoorden]
    # Burst 10: de eerste tien slagen; binnen een seconde komt er één bij, dus 429 op 11 of 12.
    remmen = [(a, l) for c, a, l in antwoorden if c == 429]
    ok = (codes[:10] == [200] * 10 and 429 in codes[10:]
          and all(herkomst(429, a, l) == "Traefik" and a.getheader("Retry-After")
                  for a, l in remmen))
    print(f"{'OK ' if ok else 'FOUT'} 12 aanroepen met hetzelfde token: {codes}; "
          f"Retry-After: {[a.getheader('Retry-After') for a, _ in remmen]}")
    return ok


if __name__ == "__main__":
    if sys.argv[1] == "tempo":
        geslaagd = tempo()
    else:
        geslaagd = status([int(c) for c in sys.argv[1].split(",")], sys.argv[2:])
    sys.exit(0 if geslaagd else 1)
