"""Client voor tests/proxy/draai.sh: draait in een container met een vast adres en roept
/api/v1/ik aan via de losse Traefik. Geeft exitcode 1 als een status afwijkt.

    klant.py <verwacht>[,<verwacht>...] [Kop: waarde | -]...   een aanroep per kop, - is zonder kop
    klant.py tempo [code]                       12 aanroepen: eerst code (standaard 200), dan 429
    klant.py iprem                              60 aanroepen vanaf een adres, dan 429 van iprem
    klant.py sein                               wacht op het sein van iprem, dan drie aanroepen
    klant.py pad <METHODE> <code> <pad>         padproef (padproeven.sh): één aanroep op PAD; bij
                                                200 moet de upstream dit pad ontvangen hebben
    klant.py rem <METHODE> <ja|nee>             25 aanroepen op PAD over één verbinding: ja is
                                                een 429 van Traefik, nee is 25 keer 200

Omgeving: DOEL (adres:poort van Traefik), SCHEMA (https of http), DOMEIN (Host-kop),
TOKEN (optioneel), PAD (standaard /api/v1/ik), WACHT=1 (wacht tot Traefik de router kent),
PROXY (clientadres in een PROXY v1-kop vóór de TLS: de container speelt load balancer),
ANDER (tweede clientadres voor iprem), SEIN (bestand waarmee iprem een tweede container start).
Het token komt nergens in de uitvoer.
"""
import http.client
import json
import os
import socket
import ssl
import sys
import time

DOEL, SCHEMA, DOMEIN = os.environ["DOEL"], os.environ["SCHEMA"], os.environ["DOMEIN"]
TOKEN = os.environ.get("TOKEN")
PAD = os.environ.get("PAD") or "/api/v1/ik"
PROXY, ANDER, SEIN = (os.environ.get(n) for n in ("PROXY", "ANDER", "SEIN"))
# Platte tekst die Traefik zelf geeft; elk ander antwoord komt van de applicatie of is onbekend.
# De 400 om een gecodeerd teken (allowencoded...=false) heeft een leeg lichaam.
TRAEFIK = {400: (b"Bad Request", b""), 403: (b"Forbidden",), 404: (b"404 page not found\n",),
           429: (b"Too Many Requests",)}
# Het standaardcertificaat van een losse Traefik is zelf ondertekend.
CONTEXT = ssl._create_unverified_context()


def verbind(proxy=PROXY):
    host, poort = DOEL.split(":")
    sock = socket.create_connection((host, int(poort)), timeout=10)
    if proxy:
        # Zoals een load balancer: de PROXY v1-kop gaat vóór de TLS over de verbinding.
        sock.sendall(f"PROXY TCP4 {proxy} {host} 40000 {poort}\r\n".encode())
    if SCHEMA == "https":
        sock = CONTEXT.wrap_socket(sock, server_hostname=host)
    verbinding = http.client.HTTPConnection(host, int(poort), timeout=10)
    verbinding.sock = sock
    return verbinding


def aanroep(kop=None, token=TOKEN, proxy=PROXY, pad=PAD, verbinding=None, methode="GET"):
    """Een aanroep over een nieuwe verbinding, of over de meegegeven (keep-alive)."""
    eigen = verbinding is None
    verbinding = verbinding or verbind(proxy)
    # skip_host: met een eigen Host-kop naast die van http.client geeft Traefik 400.
    verbinding.putrequest(methode, pad, skip_host=True)
    verbinding.putheader("Host", DOMEIN)
    if methode == "POST":
        verbinding.putheader("Content-Length", "0")
    if token:
        verbinding.putheader("Authorization", f"Bearer {token}")
    if kop:
        naam, waarde = kop.split(":", 1)
        verbinding.putheader(naam.strip(), waarde.strip())
    verbinding.endheaders()
    antwoord = verbinding.getresponse()
    lichaam = antwoord.read()
    if eigen:
        verbinding.close()
    return antwoord.status, antwoord, lichaam


def herkomst(code, antwoord, lichaam):
    """Wie antwoordde: de applicatie geeft JSON, Traefik zijn eigen platte tekst."""
    soort = antwoord.getheader("Content-Type") or ""
    if soort.startswith("application/json"):
        return "applicatie"
    # De 403 en 429 van Traefik hebben geen Content-Type, de 404 wel text/plain.
    if soort in ("", "text/plain; charset=utf-8") and lichaam in TRAEFIK.get(code, ()):
        return "Traefik"
    return f"onbekend ({soort!r}, {lichaam[:30]!r})"


def wacht():
    if os.environ.get("WACHT") == "1":
        # Traefik kent de router pas als api gezond is en het event verwerkt is; tot dan 404.
        for _ in range(40):
            if aanroep()[0] != 404:
                break
            time.sleep(0.5)


def status(verwacht, koppen):
    wacht()
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
              f"kop: {'geen' if kop == '-' else kop}; PROXY-kop: {PROXY or 'geen'}")
    return goed


def tempo(eerst="200"):
    antwoorden = [aanroep() for _ in range(12)]
    codes = [code for code, _, _ in antwoorden]
    # Burst 10: de eerste tien slagen; binnen een seconde komt er één bij, dus 429 op 11 of 12.
    remmen = [(a, l) for c, a, l in antwoorden if c == 429]
    ok = (codes[:10] == [int(eerst)] * 10 and 429 in codes[10:]
          and all(herkomst(429, a, l) == "Traefik" and a.getheader("Retry-After")
                  for a, l in remmen))
    print(f"{'OK ' if ok else 'FOUT'} {PAD}: 12 aanroepen met hetzelfde token: {codes}; "
          f"Retry-After: {[a.getheader('Retry-After') for a, _ in remmen]}")
    return ok


def pad(methode, code, echo):
    """Een aanroep op PAD. 200 komt van de upstream (echo.py) met het pad dat Traefik doorstuurde;
    een andere status moet van Traefik zelf komen."""
    wacht()
    status_, antwoord, lichaam = aanroep(methode=methode)
    bron = herkomst(status_, antwoord, lichaam)
    ontvangen = json.loads(lichaam)["pad"] if bron == "applicatie" else None
    ok = status_ == int(code) and (ontvangen == echo if status_ == 200 else bron == "Traefik")
    print(f"{'OK ' if ok else 'FOUT'} {methode} {PAD} Host {DOMEIN}: verwacht {code} "
          f"{echo if code == '200' else ''}, kreeg {status_} van {bron}; upstream: {ontvangen}")
    return ok


def rem(methode, verwacht):
    """25 aanroepen over één keep-alive verbinding (een TLS-handdruk per aanroep zou de grens
    laten bijvullen). ja: Traefik remt (429); de burst telt hier niet, want routers delen een teller
    en het aantal tokens hangt af van de tijd sinds de vorige proef. nee: 25 keer 200."""
    verbinding = verbind()
    codes = []
    for _ in range(25):
        status_, antwoord, lichaam = aanroep(verbinding=verbinding, methode=methode)
        codes.append(status_ if status_ != 429 or herkomst(429, antwoord, lichaam) == "Traefik"
                     else "429 van elders")
    verbinding.close()
    ok = (429 in codes and set(codes) <= {200, 429} if verwacht == "ja" else codes == [200] * 25)
    print(f"{'OK ' if ok else 'FOUT'} {methode} {PAD}: rem verwacht {verwacht}; {codes}")
    return ok


def van(antwoord):
    """Code en laag van een antwoord, zoals 401/applicatie."""
    code, a, lichaam = antwoord
    return f"{code}/{herkomst(code, a, lichaam)}"


def iprem():
    """De burst van iprem is 50 per adres. Elke aanroep heeft een eigen ongeldig token, dus
    tokenrem remt niet: 50 keer 401 van de applicatie, daarna 429 van Traefik. De laatste tien
    gaan over het pad met %2F: ook dat pad telt in iprem. Daarna direct een tweede adres (ANDER
    in deze container, of via SEIN in een andere): met een eigen teller krijgt dat 401."""
    # Een verbinding met keep-alive: met TLS per aanroep vult iprem (5 per seconde) bij.
    verbinding = verbind()
    tweede = verbind(ANDER) if ANDER else None
    eerst = [van(aanroep(token=f"blb_proef{i}", verbinding=verbinding)) for i in range(50)]
    # Een plek die intussen vrijkomt, laat een aanroep door; dan geeft de applicatie 400.
    gecodeerd = [van(aanroep(token=f"blb_proefpad{i}", pad="/api/v1/%2Fik",
                             verbinding=verbinding)) for i in range(10)]
    verbinding.close()
    if SEIN:
        with open(SEIN + ".tmp", "w") as f:
            f.write(str(time.time()))
        os.replace(SEIN + ".tmp", SEIN)
    ander = drie(tweede, "blb_proefander") if tweede else None
    ok = (eerst == ["401/applicatie"] * 50
          # Eén 429 bewijst dat het pad in iprem telt; anders gaf de applicatie steeds 400.
          and "429/Traefik" in gecodeerd
          and set(gecodeerd) <= {"429/Traefik", "400/applicatie"}
          and ander in (None, ["401/applicatie"] * 3))
    print(f"{'OK ' if ok else 'FOUT'} iprem vanaf {PROXY or 'eigen adres'}: 50 keer "
          f"{sorted(set(eerst))}, daarna %2F: {gecodeerd}; ander adres {ANDER}: {ander}")
    return ok


def drie(verbinding, token):
    """Drie aanroepen direct na de 429 over een open verbinding. iprem vult elke 0,2 s één plek
    bij: een gedeelde teller geeft hier dus minstens twee keer 429."""
    antwoorden = [van(aanroep(token=f"{token}{i}", verbinding=verbinding)) for i in range(3)]
    verbinding.close()
    return antwoorden


def sein():
    """Wacht op het sein van iprem uit een andere container en roept direct aan."""
    verbinding = verbind()
    for _ in range(12000):
        if os.path.exists(SEIN):
            break
        time.sleep(0.005)
    else:
        print("FOUT geen sein van iprem binnen 60 s")
        return False
    with open(SEIN) as f:
        begin = float(f.read())
    antwoord = drie(verbinding, "blb_proefsein")
    na = time.time() - begin
    ok = antwoord == ["401/applicatie"] * 3 and na < 0.2
    print(f"{'OK ' if ok else 'FOUT'} tweede adres {na:.3f} s na de 429 van het eerste: {antwoord}")
    return ok


if __name__ == "__main__":
    if sys.argv[1] in ("tempo", "iprem", "sein", "pad", "rem"):
        geslaagd = globals()[sys.argv[1]](*sys.argv[2:])
    else:
        geslaagd = status([int(c) for c in sys.argv[1].split(",")], sys.argv[2:])
    sys.exit(0 if geslaagd else 1)
