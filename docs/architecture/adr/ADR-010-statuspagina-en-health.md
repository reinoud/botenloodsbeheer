# ADR-010 Technische statuspagina en health endpoints

**Status:** Besloten door Foundation
**Datum:** 2026-10-30
**Versie:** v1.1.1
**Stories:** BLB-036, BLB-037

## Context

De applicatie meldt of ze leeft en gereed is, zonder inloggen en zonder gegevens over leden of boten (BLB-036). Een ingelogde beheerder ziet een technische statuspagina in leesbare vorm en als JSON: applicatieversie, databasestatus, laatste ledensynchronisatie met resultaat, laatste opschoning, of API en terugschrijven aan staan, en een waarschuwing voor tokens die binnen een maand verlopen (BLB-037, intake). Op die pagina staan geen tokens, wachtwoorden, inloggegevens of ledengegevens. Docker-compose heeft healthchecks nodig om containers te herstarten en volgorde te bewaken. Sinds 2026-10-31 loopt de synchronisatie als import via de API, en weet de applicatie niet welke bron de integratiecontainer gebruikt (ADR-012).

## Besluit

**Health endpoints**, zonder inloggen, alleen bereikbaar via Traefik (ADR-013):

| Endpoint | Controle | Antwoord |
|----------|----------|----------|
| `GET /health/live` | Het proces antwoordt; geen database | 200 met `{"status": "ok"}` |
| `GET /health/ready` | `SELECT 1` op de database en de migratieversie gelijk aan de verwachte head | 200 of 503 met `{"status": "ok"}` of `{"status": "niet gereed"}` |

De antwoorden bevatten geen versie, foutmelding of hostnaam: wie niet is ingelogd, krijgt alleen ok of niet gereed. Traefik zet geen rate limit op de health endpoints.

**Healthchecks in compose:** `web` en `api` op `/health/live`; `db` met `pg_isready`; `worker` met `flask taken gezond`, dat controleert of de heartbeat in `taakrun` jonger is dan 2 minuten. `web`, `api` en `worker` starten pas als `db` gezond is en `migrate` klaar is. `integratie` heeft geen healthcheck; de statuspagina laat zien of hij werkt.

**Statuspagina**, na inloggen als beheerder:

- `GET /status` (HTML) en `GET /status.json` (JSON) uit dezelfde functie, zodat ze niet uit elkaar lopen.
- Inhoud: applicatieversie (uit een buildargument in het image), databaseversie en migratieversie, laatste heartbeat van de worker, laatste import van leden via de API (tijdstip, resultaat, aantallen nieuw, bijgewerkt, oud-lid, overgeslagen, en bij een fout de reden uit de vaste lijst van ADR-012), laatste opschoning (tijdstip en aantallen), API aan of uit, laatste aanroep per robottoken, wanneer de bootaantallen voor het laatst zijn opgehaald, tokens die binnen 31 dagen verlopen met naam en vervaldatum.
- Statusregels per onderdeel: ok, waarschuwing of fout. Een heartbeat ouder dan 2 minuten, een mislukte laatste import of een geslaagde import ouder dan 26 uur geeft een waarschuwing. Die laatste vangt ook een integratiecontainer die niet draait.

**Foutmeldingen zonder geheimen.** De worker en de API leggen bij een fout alleen de foutklasse en een vaste, door de applicatie gekozen omschrijving vast, bijvoorbeeld "ledenbron onbereikbaar". Ruwe exceptieteksten van HTTP-bibliotheken kunnen URL's met inloggegevens bevatten; de integratiecontainer stuurt ze alleen geschoond naar stdout. Een test zet een herkenbaar nepgeheim in de omgeving van `integratie` en controleert dat het niet op de statuspagina en niet in `taakrun` staat (BLB-007).

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Eén health endpoint | Docker en een externe monitor willen onderscheid tussen "proces leeft" en "kan verzoeken aan"; een databasestoring mag `web` niet laten herstarten |
| Prometheus-metrics | Geen monitoringstack bij een vereniging; de statuspagina beantwoordt de vragen van de beheerder |
| Statuspagina openbaar met beperkte inhoud | Versie en status van de synchronisatie geven een aanvaller informatie; BLB-037 vraagt inloggen |
| Health van de worker via een HTTP-poort in de worker | Een extra server in de worker voor wat een rij in de database al laat zien |

## Gevolgen

- Een externe monitor van de hosting kan `/health/ready` gebruiken zonder account.
- De beheerder ziet op één pagina of import en opschoning lopen; storingen zijn niet alleen in de containerlogs te vinden. Welke bron de integratiecontainer gebruikt, staat er niet op.
- De statusfunctie leest alleen; ze is daarom ook geschikt voor een latere API-route, als daar vraag naar is.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.1.1 | 2026-10-31 | Traefik in plaats van Nginx | Besluit stakeholder 2026-10-31, issue #29 (ADR-013) |
| v1.1.0 | 2026-10-31 | Healthcheck voor `api`; statuspagina toont de laatste import via de API, de laatste aanroep per robottoken en het ophalen van de bootaantallen, niet meer de ledenbron en de instelling terugschrijven | Besluiten stakeholder 2026-10-31, ADR-012 |
| v1.0.0 | 2026-10-30 | Eerste versie | |
