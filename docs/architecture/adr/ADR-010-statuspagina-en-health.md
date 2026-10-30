# ADR-010 Technische statuspagina en health endpoints

**Status:** Besloten door Foundation
**Datum:** 2026-10-30
**Stories:** BLB-036, BLB-037

## Context

De applicatie meldt of ze leeft en gereed is, zonder inloggen en zonder gegevens over leden of boten (BLB-036). Een ingelogde beheerder ziet een technische statuspagina in leesbare vorm en als JSON: applicatieversie, databasestatus, laatste ledensynchronisatie met resultaat, laatste opschoning, of API en terugschrijven aan staan, en een waarschuwing voor tokens die binnen een maand verlopen (BLB-037, intake). Op die pagina staan geen tokens, wachtwoorden, inloggegevens of ledengegevens. Docker-compose heeft healthchecks nodig om containers te herstarten en volgorde te bewaken.

## Besluit

**Health endpoints**, zonder inloggen, alleen bereikbaar via Nginx:

| Endpoint | Controle | Antwoord |
|----------|----------|----------|
| `GET /health/live` | Het proces antwoordt; geen database | 200 met `{"status": "ok"}` |
| `GET /health/ready` | `SELECT 1` op de database en de migratieversie gelijk aan de verwachte head | 200 of 503 met `{"status": "ok"}` of `{"status": "niet gereed"}` |

De antwoorden bevatten geen versie, foutmelding of hostnaam: wie niet is ingelogd, krijgt alleen ok of niet gereed. Nginx sluit de health endpoints uit van de rate limits.

**Healthchecks in compose:** `web` op `/health/live`; `db` met `pg_isready`; `worker` met `flask taken gezond`, dat controleert of de heartbeat in `taakrun` jonger is dan 2 minuten. `web` en `worker` starten pas als `db` gezond is en `migrate` klaar is.

**Statuspagina**, na inloggen als beheerder:

- `GET /status` (HTML) en `GET /status.json` (JSON) uit dezelfde functie, zodat ze niet uit elkaar lopen.
- Inhoud: applicatieversie (uit een buildargument in het image), databaseversie en migratieversie, laatste heartbeat van de worker, laatste synchronisatie (tijdstip, resultaat, aantallen nieuw, bijgewerkt, oud-lid, overgeslagen, en bij een fout de foutmelding), laatste opschoning (tijdstip en aantallen), actieve ledenbron, API aan of uit, terugschrijven aan of uit, tokens die binnen 31 dagen verlopen met naam en vervaldatum.
- Statusregels per onderdeel: ok, waarschuwing of fout. Een heartbeat ouder dan 2 minuten, een mislukte laatste synchronisatie of een synchronisatie ouder dan 26 uur geeft een waarschuwing.

**Foutmeldingen zonder geheimen.** De worker legt bij een fout alleen de foutklasse en een vaste, door de applicatie gekozen omschrijving vast, bijvoorbeeld "ledenbron onbereikbaar (time-out)". Ruwe exceptieteksten van HTTP-bibliotheken kunnen URL's met inloggegevens bevatten en gaan alleen geschoond naar stdout. Een test zet een herkenbaar nepgeheim in de omgeving en controleert dat het niet op de statuspagina en niet in `taakrun` staat (BLB-007).

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Eén health endpoint | Docker en een externe monitor willen onderscheid tussen "proces leeft" en "kan verzoeken aan"; een databasestoring mag `web` niet laten herstarten |
| Prometheus-metrics | Geen monitoringstack bij een vereniging; de statuspagina beantwoordt de vragen van de beheerder |
| Statuspagina openbaar met beperkte inhoud | Versie en status van de synchronisatie geven een aanvaller informatie; BLB-037 vraagt inloggen |
| Health van de worker via een HTTP-poort in de worker | Een extra server in de worker voor wat een rij in de database al laat zien |

## Gevolgen

- Een externe monitor van de hosting kan `/health/ready` gebruiken zonder account.
- De beheerder ziet op één pagina of synchronisatie en opschoning lopen; storingen zijn niet alleen in de containerlogs te vinden.
- De statusfunctie leest alleen; ze is daarom ook geschikt voor een latere API-route, als daar vraag naar is.
