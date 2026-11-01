# Terugblik Sentinel, review issue #39

Datum: 2026-11-01. Taak: review van de gestagede diff "boot wijzigen" met logactie `boot.gewijzigd` (issue #39).

## Wat ging goed
- De opdracht noemde de normen, de voorrang bij botsing en de mutanten met het commando. Ik kon direct toetsen.
- De mutanten waren diffs van één regel op de gestagede versie; met `diff` tegen `git show :pad` was dat in één stap te controleren.
- De `race`-helper en de bestaande racetests maakten een proef op de slotvolgorde klein: één test van 30 regels.

## Wat kon beter
- De backlog (BLB-005) vraagt oud en nieuw voor de eigenaar; de ADR en de handleiding zeggen "gewijzigd". Die botsing zat al in de besluitcommit en kwam pas bij de review boven.
- Voor een losse proef met de fixtures moest ik een `conftest.py` in de scratchpad maken die `tests.unit.conftest` importeert. Dat staat nergens.

## Wat deed je zelf goed
- Ik heb de deadlock niet alleen beredeneerd: een proef met `FOR UPDATE NOWAIT` slaagt op de gestagede code en faalt met de oude volgorde, terwijl de 74 bestaande tests in de drie geraakte bestanden met de oude volgorde groen blijven.
- Met een mutant zonder plaatsslot in `toewijzen` heb ik laten zien dat de bestaande racetest voor dezelfde plaats nog bijt.

## Wat heb je onderweg verbeterd
- Ik heb de proef als bind mount buiten `tests/` gedraaid (`/app/proef`), zodat er geen mountpoint in de werkmap ontstond.

## Wat kan structureel beter in de opdracht of de afspraken
- Zet in de opdracht: "Wijzigt de regie na de bouw een vergrendelvolgorde, lever dan een racetest die faalt met de oude volgorde (bijvoorbeeld met `FOR UPDATE NOWAIT` op de tweede rij), of maak er een issue voor."
- Zet in de opdracht: "Loop na een besluitcommit elk criterium in de backlog na tegen de ADR-zin over hetzelfde onderwerp; een uitzondering in de ADR staat ook in het criterium."
- Zet in de opdracht: "Een losse proef met de fixtures van de unittests draai je met een `conftest.py` in de scratchpad (`from tests.unit.conftest import *`), gemount op `/app/proef` met `-e PYTHONPATH=/app`."
