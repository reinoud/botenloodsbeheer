"""Client voor tests/proxy/draai.sh: draait in een container met een vast adres en roept
/api/v1/ik aan via de losse Traefik. Geeft exitcode 1 als een status afwijkt.

    klant.py <verwacht> [Kop: waarde | -]...   een aanroep per argument, - is zonder extra kop
    klant.py tempo                              12 aanroepen achter elkaar, vanaf de 11e 429

Omgeving: DOEL (adres:poort van Traefik), SCHEMA (https of http), DOMEIN (Host-kop),
TOKEN (optioneel), WACHT=1 (wacht tot Traefik de router kent). Het token komt nergens in de uitvoer.
"""
import http.client
import json
import os
import ssl
import sys
import time

DOEL, SCHEMA, DOMEIN = os.environ["DOEL"], os.environ["SCHEMA"], os.environ["DOMEIN"]
TOKEN = os.environ.get("TOKEN")
# Het standaardcertificaat van een losse Traefik is zelf ondertekend.
CONTEXT = ssl._create_unverified_context()


def aanroep(kop=None):
    host, poort = DOEL.split(":")
    if SCHEMA == "https":
        verbinding = http.client.HTTPSConnection(host, int(poort), timeout=10, context=CONTEXT)
    else:
        verbinding = http.client.HTTPConnection(host, int(poort), timeout=10)
    # skip_host: met een eigen Host-kop naast die van http.client geeft Traefik 400.
    verbinding.putrequest("GET", "/api/v1/ik", skip_host=True)
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
    return antwoord.status, antwoord.getheader("Content-Type") or "", lichaam


def herkomst(soort, lichaam):
    """Wie antwoordde: de applicatie geeft JSON, Traefik platte tekst."""
    return "applicatie" if soort.startswith("application/json") else f"Traefik ({lichaam[:30]!r})"


def status(verwacht, koppen):
    if os.environ.get("WACHT") == "1":
        # Traefik kent de router pas als api gezond is en het event verwerkt is; tot dan 404.
        for _ in range(40):
            if aanroep()[0] != 404:
                break
            time.sleep(0.5)
    goed = True
    for kop in koppen or ["-"]:
        code, soort, lichaam = aanroep(None if kop == "-" else kop)
        bron = herkomst(soort, lichaam)
        # 200 en 401 moeten van de applicatie komen, 403 en 404 van Traefik.
        verwachte_bron = "applicatie" if verwacht in (200, 401) else "Traefik"
        ok = code == verwacht and bron.startswith(verwachte_bron)
        if code == 200 and ok:
            ok = "token" in json.loads(lichaam)
        goed &= ok
        print(f"{'OK ' if ok else 'FOUT'} verwacht {verwacht}, kreeg {code} van {bron}; "
              f"kop: {'geen' if kop == '-' else kop}")
    return goed


def tempo():
    codes = [aanroep()[0] for _ in range(12)]
    # Burst 10: de eerste tien slagen; binnen een seconde komt er één bij, dus 429 op 11 of 12.
    ok = codes[:10] == [200] * 10 and 429 in codes[10:]
    print(f"{'OK ' if ok else 'FOUT'} 12 aanroepen met hetzelfde token: {codes}")
    return ok


if __name__ == "__main__":
    if sys.argv[1] == "tempo":
        geslaagd = tempo()
    else:
        geslaagd = status(int(sys.argv[1]), sys.argv[2:])
    sys.exit(0 if geslaagd else 1)
