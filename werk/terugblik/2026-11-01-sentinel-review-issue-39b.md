# Terugblik sentinel, herreview issue #39 (boot wijzigen)

**Datum:** 2026-11-01
**Taak:** herreview van de gestagede diff voor "boot wijzigen" met `boot.gewijzigd`, na een eerder "niet akkoord".

## Wat ging goed

De opdracht noemde de drie herstelpunten met bestand, test en mutantbestanden. Daardoor kon ik elk punt direct toetsen. `git diff --stat` liet zien dat alleen `docs/` afweek, dus de gemounte code was gelijk aan de gestagede versie. Alle drie mutanten vielen om op een test, de unitsuite (370) en de E2E-tests (4) slaagden.

## Wat kon beter

`ruff` staat niet op de host. Ik moest het in de testcontainer draaien. De opdracht zegt alleen `ruff check --no-cache`, zonder plek.

De bijgewerkte ADR-006 staat niet gestaged. Als de regie alleen de gestagede paden commit, blijft de ADR-zin over de eigenaar ("als `gewijzigd`") in de commit achter bij code en handleiding.

## Wat deed ik zelf goed

Ik vergeleek eerst elke mutant met de gestagede `toewijzing.py` (`git show :`), zodat vaststond dat elke mutant precies één regel verschilt. Ik controleerde ook dat de draaiende webcontainer de nieuwe code had, voordat ik de E2E-uitslag meetelde.

## Wat heb ik onderweg verbeterd

Ik draaide de mutanten tegen beide geraakte testbestanden (`test_indeling_en_toewijzing.py` en `test_boot_wijzigen.py`), omdat de racetests van `boot_wijzigen` ook de slotvolgorde van `toewijzen` raken.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Draai ruff in de testcontainer: `docker compose -f docker-compose.yml -f compose.dev.yml run --rm test ruff check --no-cache`."

Zet in de opdracht: "Staat een bijgewerkt document voor dezelfde wijziging ongestaged, commit het in dezelfde ronde als de code."
