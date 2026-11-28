Datum: 2026-11-28. Taak: securityreview vóór commit van issue #454, padproeven van ADR-013 als script (aegis).

## Wat ging goed

- De brief noemde per bestand de securityvraag (labels van productie, standaard van Traefik, bindadres van echo.py). Daardoor kon ik gericht lezen.
- De uitvoer van de bouwer (`run-groen.txt`) liet per proef de ontvangen upstream en de tellingen van de rate limit zien. Ik kon de verwachtingen toetsen zonder zelf te draaien.
- `werk/traefik-proeven.md` (herhaling v3.7.18) gaf de lijst om het script tegen af te vinken.

## Wat kon beter

- De brief vroeg of de standaard van Traefik echt ongewijzigd is, maar verbood Docker-proeven. Ik heb `traefik --help` uit het lokale image gelezen in een container zonder netwerk. Dat is geen proef, maar de grens stond niet in de brief.

## Wat deed je zelf goed

- De standaard van alle zeven opties `allowencoded...` in v3.7.18 vastgesteld met `--help` (overal `true`), in plaats van op het commentaar in `compose.traefik.yml` te vertrouwen.
- Nagegaan wie `compose.traefik.yml` leest (`draai.sh`, `padproeven.sh`, en `test_integratie.py` alleen voor het image), zodat de vraag over productie met bewijs beantwoord is.
- Per negatieve verwachting nagegaan of een regressie in Traefik groen kan blijven, met de tellingen uit de run (25 aanroepen tegen burst 20).

## Wat heb je onderweg zelf verbeterd

- Eerst dacht ik dat de verbrede `TRAEFIK[400]` in `klant.py` een controle in `draai.sh` kon verzwakken. De 400-controles daar eisen herkomst `applicatie` (JSON), dus een lege 400 telt daar niet als geslaagd. Dat punt heb ik laten vallen.

## Wat kan structureel beter in de opdracht of de afspraken

- Zet in de opdracht: "Docker-proeven zijn verboden, maar een `--help` of `version` uit een lokaal image met `--network none --pull never` mag, om de standaardwaarde van een optie vast te stellen."
