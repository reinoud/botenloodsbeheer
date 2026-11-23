# Terugblik Sentinel, review #378 (vaste override voor de release-E2E)

**Datum:** 2026-11-23
**Taak:** de gestagede diff van #378 toetsen (`tests/e2e/compose.release.yml`, commentaar in `tests/e2e/draai.sh`, overlay v0.6.24), statisch en met `docker compose config`, plus de samenvatting van de proefrun van pipeline. Oordeel: akkoord.

## Wat ging goed

De opdracht noemde vier concrete toetsvragen en de plek van de proefrunlogs. Daardoor was de review in een paar stappen klaar. `docker compose config --services` met `--profile '*'` liet in één keer zien dat de override geen dienst mist: tien diensten in de basis, tien in de release. De gerenderde JSON gaf per dienst image, build en poorten. Geen dienst heeft nog een binding naar de host, en zonder of met een lege `RELEASE_TAG` stopt `config` met "RELEASE_TAG ontbreekt".

## Wat kon beter

Vraag 3 (kan `build:` het releaseimage overschrijven) had een antwoord dat al in de overlay stond: de regel over `up -d --no-build --wait` voor een eigen E2E-stack (#321) staat twee regels boven de releaseregel. Met die verwijzing in de opdracht had ik niet hoeven zoeken.

## Wat deed ik zelf goed

Ik heb de telling van de proefrun met een script opgeteld en niet uit het log overgenomen: 27 pytest-runs, 59 geslaagd, 0 gefaald, 0 overgeslagen, tegen 27 testbestanden en 59 testfuncties. Ook heb ik in `inspect-api.json` nagekeken dat api echt op `botenloods-app:pl378` draaide.

## Wat heb ik onderweg zelf verbeterd

Eerst wilde ik de basisdiensten vergelijken zonder profielen. Dan vallen `test`, `test-integratie` en `e2e` weg. Met `--profile '*'` komen ze mee, zodat ook de profieldiensten in de vergelijking zitten.

## Wat kan structureel beter in de opdracht of de afspraken

Twee kleine punten, geen van beide blokkerend. De override neemt `e2e` uit de lokale stack (`botenloods-e2e`); brengt een release een bump in `tests/e2e/requirements.txt` of de `Dockerfile` daar, dan draait de E2E met de oude runner. En `RELEASE_TAG` is nodig bij elke compose-aanroep met dit bestand, ook bij `logs` en `down -v`, niet alleen bij `up` en `draai.sh`.

Zet in de opdracht: "Raakt de release `tests/e2e/Dockerfile` of `tests/e2e/requirements.txt`, bouw dan ook `botenloods-e2e` opnieuw vóór de run, en zet `RELEASE_TAG` bij elke compose-aanroep op het releaseproject."
