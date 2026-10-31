# Integratiecontainer

**Versie:** v1.0.0
**Datum:** 2026-10-31
**Opgesteld door:** Forge, Lead Developer
**Bronnen:** ADR-004, ADR-012, `app/api/openapi.yaml`

De integratiecontainer haalt de leden uit de ledenbron en stuurt ze naar de applicatie. Hij praat alleen met de API, over het interne netwerk `koppeling`, via de interne Nginx-server op `http://nginx:8081/api/v1`. Hij bereikt de database en de dienst `api` niet rechtstreeks. De inloggegevens van de bron staan alleen in zijn omgeving; de applicatie kent ze niet.

## Werking

De container draait een ronde per minuut. Hij vraagt of een beheerder een import heeft aangevraagd (de knop "Leden nu ophalen" op de pagina Leden). Is dat zo, of is `SYNC_TIJDSTIP` gepasseerd en slaagde die dag nog geen import, dan haalt hij de leden op en stuurt hij de volledige lijst met `PUT /api/v1/leden`. Na een fout probeert hij het hooguit één keer per uur opnieuw, ook bij een verzoek van een beheerder. Een nieuw token heft die wachttijd op.

De uitkomst van elke import staat op de pagina Leden, met de aantallen of de reden van de fout. Wijzigingen in leden komen niet in het mutatielog.

| Variabele | Standaard | Betekenis |
|-----------|-----------|-----------|
| `LEDENBRON` | leeg | `stub` of leeg. Leeg: de container meldt dat er geen bron is en roept de API niet aan |
| `LEDENBRON_STUB_BESTAND` | `/data/leden.json` | JSON-bestand van de stub, alleen voor ontwikkeling en tests |
| `SYNC_TIJDSTIP` | `03:00` | Tijdstip van de dagelijkse import, in de tijdzone `TZ` |
| `API_URL` | `http://nginx:8081/api/v1` | Adres van de API; staat vast in `docker-compose.yml` |
| `API_TOKEN_FILE` | `/run/secrets/api_token` | Het token; compose levert `secrets/api_token` als secret |

## Token maken en instellen

Het token is een robottoken met alleen de rechten `leden:importeren` en `bootaantallen:lezen`. De whitelist is standaard het netwerk `koppeling` (`KOPPELNET`) en het token is 365 dagen geldig.

1. Maak het bestand voor het token, ook als er nog geen token is. Zonder dat bestand start compose niet:

   ```sh
   mkdir -p secrets && install -m 600 /dev/null secrets/api_token
   ```

2. Maak het token in de dienst `web` en zet het in het bestand:

   ```sh
   docker compose exec -T web flask token robot integratie \
     --recht leden:importeren --recht bootaantallen:lezen 2>/dev/null | tail -n 1 > secrets/api_token
   ```

   De CLI toont het token één keer en schrijft een logregel met actor `cli`, zonder het token.

3. Op Linux leest de container het bestand als gebruiker 10001. Geef die gebruiker het bestand:

   ```sh
   sudo chown 10001 secrets/api_token
   ```

4. Start de container met `docker compose up -d integratie`. Bij de volgende ronde gebruikt hij het token; een herstart is niet nodig.

Zonder token schrijft de container elke minuut "Geen token in /run/secrets/api_token" in zijn log.

## Token vernieuwen of intrekken

Vernieuwen is een nieuw token maken en het oude intrekken. Maak het nieuwe token onder een andere naam, bijvoorbeeld `integratie-2027`, zet het in `secrets/api_token` zoals hierboven, en trek daarna het oude in:

```sh
docker compose exec web flask token intrekken integratie
```

De container gebruikt het nieuwe token bij de volgende ronde. Een ingetrokken token weigert de API bij de volgende aanroep.

## De aanroepen

De container gebruikt vier aanroepen. Elke aanroep heeft de header `Authorization: Bearer <token>` nodig en komt van een adres in de whitelist van het token. Een weigering geeft 401 of 403 met `{"fout": "Geen toegang."}`; meer dan 60 aanroepen per minuut geeft 429. Het volledige contract staat in `app/api/openapi.yaml`. De vijfde aanroep uit ADR-012, `GET /api/v1/bootaantallen`, komt in slice 9 (BLB-009).

De voorbeelden gebruiken alleen de standaardbibliotheek van Python, net als de container. Het token in de voorbeelden is nep.

```python
import json
import urllib.error
import urllib.request

API = "http://nginx:8081/api/v1"
TOKEN = "blb_VOORBEELDVOORBEELDVOORBEELDVOORBEELDVOORBEELDVOORBEELDVOORBE"


def roep(methode, pad, gegevens=None):
    verzoek = urllib.request.Request(
        API + pad, method=methode,
        data=json.dumps(gegevens).encode() if gegevens is not None else None,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(verzoek, timeout=60) as antwoord:
            return antwoord.status, json.loads(antwoord.read())
    except urllib.error.HTTPError as fout:
        return fout.code, json.loads(fout.read())
```

| Aanroep | Recht | Antwoord |
|---------|-------|----------|
| `GET /ik` | elk geldig token | 200 met naam, rechten en vervaldatum |
| `GET /leden/importverzoek` | `leden:importeren` | 200 met `{"aangevraagd": true}` of `false` |
| `PUT /leden` | `leden:importeren` | 200 met de aantallen; 409, 413 of 422 bij een fout |
| `POST /leden/import-mislukt` | `leden:importeren` | 201; 422 bij een andere reden |

**Token controleren.**

```python
roep("GET", "/ik")
# (200, {"token": "integratie", "rechten": ["leden:importeren", "bootaantallen:lezen"],
#        "verloopt_op": "2027-10-31"})
```

**Importverzoek opvragen.** Een verzoek blijft openstaan tot de volgende import of foutmelding het afsluit.

```python
roep("GET", "/leden/importverzoek")  # (200, {"aangevraagd": False})
```

**Leden sturen.** Stuur altijd de volledige lijst. Een lid dat ontbreekt, wordt oud-lid met de datum van die import als opzegdatum. Datums staan als `JJJJ-MM-DD`; een opzegdatum mag in de toekomst liggen.

```python
leden = [{"lidnummer": "1001", "naam": "Anna Voorbeeld", "adres": "Proefweg 1, 1234 AB Voorbeelddorp",
          "telefoon": "06-00000000", "email": "anna@example.org", "lid_sinds": "2020-04-01",
          "opzegdatum": None}]
roep("PUT", "/leden", {"leden": leden})
# (200, {"ontvangen": 1, "nieuw": 1, "bijgewerkt": 0, "uit_bron": 0, "ongeldig": 0,
#        "overgeslagen": 0})
```

De API weigert de lijst in deze gevallen, en wijzigt dan geen enkel lid:

| Status | Reden |
|--------|-------|
| 409 | Er loopt al een import |
| 409 | De lijst bevat minder dan de helft van het aantal actieve leden (veiligheidsgrens); dit staat als mislukte import op de pagina Leden |
| 413 | Het verzoek is groter dan 2 MB |
| 422 | `leden` is geen lijst, of heeft meer dan 5000 records |

Een record zonder geldig lidnummer of naam, of met een ongeldige datum of e-mail, slaat de API over en telt het als `ongeldig`. Een nieuw record met een opzegdatum van meer dan 5 jaar geleden telt als `overgeslagen`; zo komt een opgeschoond oud-lid niet terug.

**Een fout van de bron melden.** De reden komt uit een vaste lijst: `bron_onbereikbaar`, `bron_onleesbaar` of `bron_geweigerd`. De pagina Leden toont een vaste tekst bij die reden, nooit tekst van de bron.

```python
roep("POST", "/leden/import-mislukt", {"reden": "bron_onbereikbaar"})  # (201, {})
```

## Een eigen container

Een vereniging die niet met e-boekhouden werkt, kan de container vervangen door een eigen container. De applicatie blijft dan ongewijzigd. Een eigen container doet dit:

- hij draait op het netwerk `koppeling` en gebruikt alleen de vier aanroepen hierboven;
- hij leest het token uit `/run/secrets/api_token` bij elke ronde opnieuw en schrijft het nooit in zijn log;
- hij stuurt de volledige ledenlijst met `PUT /leden`, dagelijks en binnen een minuut na een importverzoek;
- hij meldt een storing van de bron met `POST /leden/import-mislukt` en een reden uit de lijst;
- hij probeert het na een fout hooguit één keer per uur opnieuw;
- hij logt geen gegevens van leden en geen inloggegevens van de bron;
- hij draait zonder root en met een alleen-lezen bestandssysteem.

De meegeleverde container in `integratie/` is het voorbeeld: `integratie/koppeling/__init__.py` bevat de lus en de aanroepen, `integratie/koppeling/bronnen.py` de bron. Een nieuwe bron in die container is één klasse in `bronnen.py` met de methode `haal_leden()` en een waarde voor `LEDENBRON`.

## Lokaal proberen met de stub

`compose.dev.yml` zet `LEDENBRON=stub` en koppelt de synthetische leden uit `tests/fixtures/leden.json`. Na de stappen onder "Token maken en instellen" importeert de container binnen een minuut 208 leden; de 2 leden die langer dan 5 jaar geleden opzegden, slaat de API over. Daarna vult `docker compose exec worker flask seed` de loods. `tests/e2e/draai.sh` doet deze stappen zelf.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.0.0 | 2026-10-31 | Eerste versie | BLB-040, slice 6 |
