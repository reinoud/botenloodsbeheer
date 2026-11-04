# Terugblik foundation: ADR-003 voor issue #83

**Datum:** 2026-11-04
**Taak:** ADR-003 bijwerken naar v2.2.0 (bootsoort per verdieping, plaats verwijderen vervalt), architectuur.md bijwerken.

## Wat ging goed

De bronvolgorde en de lijst met te besluiten punten waren scherp. Het issue noemde de verouderde zinnen in ADR-003 letterlijk, dus er was geen zoekwerk naar wat moest wijzigen.

## Wat kon beter

Het budget van 300 woorden was krap voor vijf besluitpunten plus migratie en alternatieven. De eerste versie telde 437 woorden en moest in twee rondes worden ingekort. Daarbij viel de zin over bestaande plaatsen eerst weg en moest terug.

## Wat deed ik zelf goed

Ik heb `bootsoort_verwijderen` gelezen voordat ik koos tussen weigeren en cascade. Weigeren had een bootsoort onverwijderbaar gemaakt, omdat geen scherm de keuze per verdieping wist. Ik heb ook gecontroleerd dat de rol `botenloods_web` per migratie expliciete rechten krijgt, zodat de migratie de grant moet noemen.

## Wat heb ik onderweg verbeterd

In architectuur.md stond nog dat de indeling alleen de plaatsen vergrendelt die verdwijnen. Sinds ADR-003 v2.1.1 zijn dat alle plaatsen van het rek; dat heb ik meegenomen.

## Wat kan structureel beter

Zet in de opdracht: "Het woordbudget telt alleen ADR-tekst; noem per besluitpunt of een korte zin volstaat, of verhoog het budget als er meer dan vier besluitpunten zijn."
