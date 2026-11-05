# Terugblik sentinel, review issue #94

**Datum:** 2026-11-05
**Taak:** review van de gestagede diff op `feature/94-rekoverzicht-compact` (rekoverzicht zonder lege kolommen en verdiepingen, geen gaten in een verdieping)

## Wat ging goed

De brief noemde de niet-gestagede bestanden, de mutantcommando's van de bouwer en de bekende open punten. Daardoor kon ik een mutant kiezen die de bouwer nog niet had gedraaid (eerste in plaats van laatste ontbrekend vak); die viel op `test_een_gat_in_een_verdieping_wordt_geweigerd_bij_aanmaken_en_wijzigen[tweede_verdieping]`.

## Wat kon beter

De brief vroeg om `draai.sh -k test_rekoverzicht`; dat selecteert één test. Het E2E-scenario voor de weigering van een gat staat in `test_indeling.py`. Dat heb ik er zelf bij gedraaid.

## Wat deed ik zelf goed

De seed met een script nagelopen (229 plaatsen, 30 clubplaatsen, geen gaten, hoogste vak en verdieping per rek tegen de route voor een mens). Vóór de E2E-run gecontroleerd dat `web` na de laatste wijziging aan template en CSS is gestart.

## Wat heb ik onderweg verbeterd

Bij het zoeken naar oude termen kwam vraag 22 in de backlog boven ("gaten in de nummering mogen"); die staat er zonder verwijzing naar #94. Gemeld als restpunt, niet blokkerend.

## Wat kan structureel beter

Zet in de opdracht: noem bij een review naast het E2E-bestand van het scherm ook de E2E-test die het geweigerde pad bewijst, met de naam voor `draai.sh -k`.
