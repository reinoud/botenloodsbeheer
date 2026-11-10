# Terugblik sentinel, review #203

**Datum:** 2026-11-10
**Taak:** review vóór commit van issue #203 (geen nieuw oud-lid bij de import, migratie 0020)

## Wat ging goed

De brief noemde wat de regie na de bouwer had hersteld en welke mutanten al gevangen waren. Daardoor kon ik gericht de ontbrekende kanten draaien: de morgen-kant van de import, de morgen-kant van de migratie en het bestaande lid dat opzegt. De unitsuite (1191 passed) en de drie mutanten liepen zonder verstoring, omdat alleen ik de suite draaide.

## Wat kon beter

De brief vroeg naar de tijdzone van de migratie, maar noemde de tijdzone van de database niet. Die moest ik zelf opvragen (Etc/UTC). De verouderde verwijzing in ADR-006 regel 55 ("dezelfde grens als in de import") viel buiten de gestagede bestanden en kwam alleen boven met een zoekactie op de oude formulering.

## Wat deed ik zelf goed

Elke mutant draaide als bind mount tegen het hele testbestand, met de diff, het commando en de uitvoer in de scratchpad, en per mutant de falende assert als bestand:regel. Vóór de mutanten heb ik gecontroleerd dat de alembic-head 0020 is en dat GET /leden alle leden zonder paginering teruggeeft, zodat de E2E-berekening klopt.

## Wat heb ik onderweg verbeterd

Ik wilde eerst een mutant met een extra import van `timedelta` maken. Ik heb er `date.fromordinal(dag.toordinal() + 1)` van gemaakt, zodat de mutant alleen de vergelijking verandert en niets anders in het bestand.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Wijzigt een diff een regel uit een ADR, laat de reviewer dan in alle ADR's en documentatie zoeken naar verwijzingen naar die regel en naar de oude formulering, ook buiten de gestagede bestanden."

Zet in de opdracht: "Rekent een migratie met CURRENT_DATE, noem dan de tijdzone van de database (`SHOW timezone`) en die van de installatie (`TZ`)."
