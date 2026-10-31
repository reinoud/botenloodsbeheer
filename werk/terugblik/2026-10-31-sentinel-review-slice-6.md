# Terugblik Sentinel, review slice 6

**Datum:** 2026-10-31
**Taak:** review van de gestagede diff van slice 6 (tests, mutanten, migratie 0006, E2E, Nginx-log)

## Wat ging goed

De brief noemde de verwachte waarden, de ADR's en de controles (mutanten met `cmp`, eigen database, `-k`, Nginx-log). Daardoor kon ik zonder vragen toetsen. De tests van forge waren sterk: alle 13 mutanten faalden.

## Wat kon beter

De eerste mutantenronde gaf lege uitkomsten, omdat `tail -1` een lege regel pakte. Dat kostte een extra ronde.

## Wat deed ik zelf goed

Mutanten heb ik niet in de werkmap gezet, maar als bind mount over het gestagede bestand in de testcontainer (`run -v mutant:/app/<pad>:ro`). De werkmap en de gedeelde stack bleven onaangeroerd; `cmp` bevestigde dat. De downgrade liep op een eigen database, die ik daarna heb verwijderd.

## Wat heb ik onderweg verbeterd

De uitkomst van een mutant filter ik nu op `FAILED|ERROR|passed|failed` in plaats van de laatste regel.

## Wat kan structureel beter

Zet in de opdracht: "Een mutant draai je als bind mount over het bestand in de testcontainer (`docker compose ... run --rm -v <scratchpad>/mutant.py:/app/<pad>:ro test pytest ...`), niet in de werkmap; zo raakt hij de draaiende stack niet."

Zet in de opdracht: "Bij de Nginx-logcontrole tellen regels uit de foutlog (zoals `client intended to send too large body`) apart; meld of zo'n regel gewenst is."
