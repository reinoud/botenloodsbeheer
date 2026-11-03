# Terugblik foundation, ontwerp slice 10

**Datum:** 2026-11-03
**Taak:** ontwerp van slice 10 (issue #51) in ADR-005, ADR-012 en ADR-013, met criteria in de backlog

## Wat ging goed

De brief noemde bronnen, grenzen en woordbudget per ADR. Daardoor was snel duidelijk waar elk besluit hoorde en wat niet aangeraakt mocht worden.

## Wat kon beter

Het model `Token` bleek geen kolom voor de eigenaar of de maker te hebben, terwijl ADR-005 zegt dat een robottoken onthoudt wie het maakte. Dat stond nergens als open punt; ik vond het pas in `app/models.py`.

## Wat deed je zelf goed

Ik heb de code en de rechten per databaserol gelezen voordat ik velden en grants vastlegde, en elke nieuwe naam (`API_EXTERN_BRONNEN`, `externtoegang`, `eigenaar_inactief`, migratie 0009) op botsingen gecontroleerd.

## Wat heb je onderweg verbeterd

Ik liet een veld `wachttijd_dagen` weg dat ik niet tegen de domeincode kon controleren, en koos een middlewarenaam die niet lijkt op `koppeling/bronnen.py`.

## Wat kan structureel beter in de opdracht

Zet in de opdracht: "Noem per ADR-zin die de opdracht als gebouwd aanneemt (zoals een kolom of een check) of die al in `app/models.py` en de migraties staat; zo niet, dan is het een ontwerppunt van deze opdracht."
