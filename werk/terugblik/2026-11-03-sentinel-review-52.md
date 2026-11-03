# Terugblik Sentinel, review issue #52

**Datum:** 2026-11-03
**Taak:** review van de gestagede diff voor #52 (leden:importeren alleen via de CLI) met de vier restpunten uit slice 10

## Wat ging goed

De opdracht noemde de bron die leidend is, de mutanten en de commando's. Daardoor kon ik de mutanten direct draaien en hoefde ik niets te reconstrueren.

## Wat kon beter

Tijdens de review verscheen een niet-gestagede wijziging in `docs/product/backlog.md` (v0.3.21, een criterium over bootsoorten). Die hoort niet bij #52, maar een `git commit -a` zou hem meenemen.

## Wat deed je zelf goed

Ik heb de nieuwe controle in `tests/e2e/draai.sh` los gedraaid en ook tegen een mutant van `compose.api-extern.yml` zonder `:?`. Die mutant faalt zoals bedoeld. Zo staat vast dat de controle iets toetst.

## Wat heb je onderweg verbeterd

Ruff gaf in de testcontainer een cachefout (alleen-lezen `/app`). Met `--no-cache` liep de controle wel.

## Wat kan structureel beter in de opdracht

Zet in de opdracht: "Ruff in de testcontainer draait met `--no-cache`. Commit alleen de gereviewde paden, want parallelle agents wijzigen documenten in dezelfde werkmap."
