# Integratiecontainer

**Versie:** v2.0.0
**Datum:** 2026-10-31
**Bronnen:** ADR-004, ADR-012, ADR-013, `app/api/openapi.yaml`

De integratiecontainer haalt de leden uit de ledenbron en stuurt ze naar de API, via het entrypoint `intern` van Traefik over het netwerk `koppeling`. De database en de dienst `api` bereikt hij niet. De inloggegevens van de bron staan alleen in zijn omgeving.

## Werking

Elke minuut vraagt de container of een beheerder een import heeft aangevraagd ("Leden nu ophalen" op de pagina Leden). Is dat zo, of is `SYNC_TIJDSTIP` gepasseerd zonder geslaagde import die dag, dan stuurt hij de ledenlijst. Na een fout probeert hij het hooguit één keer per uur opnieuw; een nieuw token heft die wachttijd op. De uitkomst staat op de pagina Leden.

| Variabele | Standaard | Betekenis |
|-----------|-----------|-----------|
| `LEDENBRON` | leeg | `stub` of leeg; leeg roept de API niet aan |
| `LEDENBRON_STUB_BESTAND` | `/data/leden.json` | JSON-bestand van de stub, alleen voor ontwikkeling |
| `SYNC_TIJDSTIP` | `03:00` | dagelijkse import, in de tijdzone `TZ` |
| `API_URL` | `http://traefik:8081/api/v1` | adres van de API |
| `API_TOKEN_FILE` | `/run/secrets/api_token` | het token, uit `secrets/api_token` |

## Token maken

Het token is een robottoken met alleen `leden:importeren` en `bootaantallen:lezen`, 365 dagen geldig, met `KOPPELNET` als whitelist.

```sh
docker compose exec -T web flask token robot integratie \
  --recht leden:importeren --recht bootaantallen:lezen 2>/dev/null | tail -n 1 > secrets/api_token
sudo chown 10001 secrets/api_token   # Linux: de container draait als gebruiker 10001
```

De container gebruikt het token bij de volgende ronde, zonder herstart. Zonder token schrijft hij elke minuut "Geen token in /run/secrets/api_token" in zijn log. Vernieuwen en intrekken staan in [bijwerken](bijwerken.md).

## De aanroepen

Elke aanroep vraagt `Authorization: Bearer <token>` en een adres in de whitelist. Een weigering geeft 401 of 403 met `{"fout": "Geen toegang."}`. Meer dan 60 aanroepen per minuut per token, of 300 per adres, geeft 429 van Traefik met `Retry-After`, als platte tekst: lees alleen de status.

| Aanroep | Recht | Antwoord |
|---------|-------|----------|
| `GET /ik` | elk geldig token | 200 met naam, rechten en vervaldatum |
| `GET /leden/importverzoek` | `leden:importeren` | 200 met `{"aangevraagd": true}` of `false` |
| `PUT /leden` | `leden:importeren` | 200 met de aantallen; 409, 413 of 422 bij een fout |
| `POST /leden/import-mislukt` | `leden:importeren` | 201; 422 bij een onbekende reden |

Een voorbeeld in Python, met een nep-token:

```python
import json, urllib.error, urllib.request

API = "http://traefik:8081/api/v1"
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
        return fout.code, fout.read()

roep("GET", "/leden/importverzoek")  # (200, {"aangevraagd": False})
leden = [{"lidnummer": "1001", "naam": "Anna Voorbeeld", "adres": "Proefweg 1, 1234 AB Voorbeelddorp",
          "telefoon": "06-00000000", "email": "anna@example.org", "lid_sinds": "2020-04-01",
          "opzegdatum": None}]
roep("PUT", "/leden", {"leden": leden})
# (200, {"ontvangen": 1, "nieuw": 1, "bijgewerkt": 0, "uit_bron": 0, "ongeldig": 0, "overgeslagen": 0})
roep("POST", "/leden/import-mislukt", {"reden": "bron_onbereikbaar"})  # (201, {})
```

Stuur altijd de volledige lijst: een lid dat ontbreekt, wordt oud-lid. De API weigert de hele lijst, zonder iets te wijzigen, bij een lopende import (409), bij minder dan de helft van het aantal actieve leden (409, de veiligheidsgrens), boven 2 MB (413) en bij meer dan 5000 records (422). Een ongeldig record telt als `ongeldig`. Een nieuw record met een opzegdatum van meer dan 5 jaar geleden telt als `overgeslagen`, zodat een opgeschoond oud-lid niet terugkomt.

## Export van bootaantallen (nog niet gebouwd)

De export van het aantal boten per bootsoort per lid is voorbereid. Het token heeft het recht `bootaantallen:lezen` al, maar `GET /api/v1/bootaantallen` bestaat nog niet; die komt in slice 9 (BLB-009). Volgens het ontwerp levert hij per lid elke bootsoort met het aantal, ook 0. Alleen boten met een toegewezen plaats tellen, clubboten niet (besluit 2026-10-31). Terugschrijven naar de bron kan de meegeleverde container niet: `schrijf_bootaantallen` geeft `NietBeschikbaar`.

## Een eigen container bouwen

Een vereniging zonder e-boekhouden vervangt deze container door een eigen container; de applicatie blijft gelijk. Die container:

- draait op `koppeling` en gebruikt alleen de aanroepen hierboven, via `API_URL`;
- leest het token elke ronde opnieuw uit `/run/secrets/api_token` en schrijft het nooit in zijn log;
- stuurt de volledige lijst dagelijks en binnen een minuut na een importverzoek;
- meldt een storing van de bron met `POST /leden/import-mislukt`;
- probeert het na een fout hooguit één keer per uur opnieuw;
- logt geen gegevens van leden en geen inloggegevens van de bron;
- draait zonder root en met een alleen-lezen bestandssysteem.

Het voorbeeld is `integratie/`: `koppeling/__init__.py` bevat de lus, `koppeling/bronnen.py` de bron. Een nieuwe bron is één klasse met `haal_leden()` en een eigen waarde voor `LEDENBRON`. Zet bij de dienst `integratie` het eigen image en de inloggegevens van de bron in een aanvullend compose-bestand.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v2.0.0 | 2026-10-31 | Verplaatst uit `docs/beheer/`; via Traefik; export van bootaantallen; ingekort | ADR-013, issue #30 |
| v1.0.0 | 2026-10-31 | Eerste versie | BLB-040, slice 6 |
