# Terugblik: review issue #145

Datum: 2026-11-06. Taak: review van de gestagede diff voor issue #145 (reknaam in test_wachtlijst.py).

## Wat ging goed
De diff was één regel en het issue had heldere acceptatiecriteria. De review was snel rond.

## Wat kon beter
Het voorgeschreven commando `grep -on 'reknaam('` toont alleen `reknaam(` en niet de letter. Daarmee is criterium 1 niet te controleren.

## Wat deed je zelf goed
Ik heb de grep uitgebreid tot `reknaam\([^)]*\)` en de regels met een dubbele letter nagelezen. Dat zijn steeds hetzelfde rek en de bootnaam in één test, geen botsing.

## Wat heb je onderweg verbeterd
Ik heb de letter ook getoetst aan de regex in opruimen.sql (`^[a-z]` plus stempel). De letter c valt eronder.

## Wat kan structureel beter in de opdracht
Zet in de opdracht: controleer unieke reknamen met `grep -onE 'reknaam\([^)]*\)' tests/e2e/*.py`; een herhaling binnen één test (rek plus bootnaam) telt niet als dubbel.
