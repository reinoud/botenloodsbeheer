# Terugblik sentinel, review issue #84

Datum: 2026-11-04. Taak: review van de gestagede racetests en rollbacktest in `tests/unit/test_indeling_vakken.py` (issue #84). Oordeel: akkoord.

## Wat ging goed

De brief noemde de mutanten, het commando, het voorbeeld van de racetest en het aantal tests van de suite. Daardoor kon ik direct herhalen en vergelijken: 3 mutanten gevangen, suite 686 geslaagd, 0 mislukt, 0 errors, 0 overgeslagen.

## Wat kon beter

De mutant zonder rollback valt op een `OperationalError` (LockNotAvailable) en niet op een assert met een eigen melding. Dat is herkenbaar, maar een reviewer moet de foutregel lezen om te zien waarom de test valt.

## Wat deed ik zelf goed

Ik controleerde per test of hij vals-groen kan zijn: `race()` toetst het wachten zelf (`draad.is_alive()`), en bij een draad die na 5 seconden nog loopt, valt de slotassert op de soorten of op het aantal rekken alsnog. De nieuwe tests draaide ik drie keer apart om flakiness uit te sluiten.

## Wat heb ik onderweg verbeterd

Mijn eerste lus toonde alleen de laatste regel van de uitvoer, en die was leeg door de logregels van de app. Daarna heb ik gefilterd op `^E`, `FAILED` en de telregel.

## Wat kan structureel beter

Zet in de opdracht: "Een test die een mutant moet vangen, faalt op een assert met een eigen melding; een databasefout als faalreden noemt de reviewer apart."
Zet in de opdracht: "Filter de uitvoer van een mutantrun op `^E |FAILED|passed|failed`, want de laatste regel kan een logregel zijn."
