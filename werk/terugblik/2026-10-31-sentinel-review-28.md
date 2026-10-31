# Terugblik Sentinel, review issue #28

**Datum:** 2026-10-31
**Taak:** review van de gestagede fix voor issue #28 (verzoek van een beheerder wacht na een fout niet het uur af)

## Wat ging goed

De diff was klein en de brief gaf de norm, de uitzondering en de commando's voor mutanten, unitsuite en E2E. Daardoor kon ik direct gericht toetsen.

## Wat kon beter

De eerste E2E-run faalde met HTTP 404 op `nginx:8081`: na `up --build` waren `api` en `web` vernieuwd, maar nginx draaide nog met de oude upstream. Pas na `restart nginx` slaagde de test. De brief noemde dat niet.

## Wat deed je zelf goed

Zeven mutanten gedraaid, waaronder één per weigercode. Daaruit bleek dat 403 en 429 niet gedekt zijn; zonder die mutanten was dat niet opgevallen.

## Wat heb je onderweg zelf verbeterd

Ruff draaide in de testcontainer niet door een cachemap zonder schrijfrecht; met `--no-cache` wel.

## Wat kan structureel beter

Zet in de opdracht: na `docker compose ... up --build -d` ook `docker compose ... restart nginx`, anders geeft de API via nginx een 404. Zet in de opdracht: ruff in de testcontainer draait met `ruff check --no-cache`. Zet in de opdracht: een uitzondering op een besluit van de stakeholder komt ook in het acceptatiecriterium van de backlog, niet alleen in de ADR.
