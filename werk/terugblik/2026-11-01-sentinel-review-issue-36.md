# Terugblik Sentinel: review van de gestagede diff voor issue #36

**Datum:** 2026-11-01
**Taak:** review vóór commit van ADR-013 v1.1.0, architectuur v0.4.1, `openapi.yaml`, het Traefik-voorbeeld, `installatie.md` en een docstring in `tests/e2e/test_api.py`.

## Wat ging goed

De opdracht noemde de leidende bronnen en de commando's voor de drie controles. Daardoor kon ik elke tekstwijziging direct naast `compose.dev.yml`, `docker-compose.yml`, `app/config.py` en `werk/traefik-proeven.md` leggen. De openapi-test (1 geslaagd, 329 niet geselecteerd) en `compose config` met een dummy voor `ACME_EMAIL` slaagden zonder de draaiende stack te raken.

## Wat kon beter

Tijdens de review verscheen een niet-gestagede wijziging in `docs/PROJECT-OVERLAY.md`, van een andere sessie. Die raakte de review niet, maar de testcontainer mount de werkmap en niet de staging. Een gelijktijdige wijziging in `app/` had de testuitkomst stil kunnen veranderen.

## Wat deed je zelf goed

Ik heb vóór de testrun gecontroleerd dat `app/` geen niet-gestagede wijzigingen had, zodat de test de gestagede versie toetste. Ik heb ook gezocht naar oude termen (`docker/traefik`, `text/plain`, de oude aanbeveling) buiten `werk/`.

## Wat heb je onderweg zelf verbeterd

Ik heb de lokale Traefik in `compose.dev.yml` naast de nieuwe eis `aliasHeadersStrategy=delete` gelegd. Die staat lokaal niet aan. Ik meld dat als opmerking zonder blokkade: de E2E-test toetst zo juist de zwakkere opstelling.

## Wat kan structureel beter

Zet in de opdracht: "Controleer vóór een testrun met `git diff --stat` dat de gemounte paden geen niet-gestagede wijzigingen hebben; anders toetst de test niet de gestagede diff."
