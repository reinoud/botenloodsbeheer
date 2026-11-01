# Terugblik Sentinel: review issue #42

**Datum:** 2026-11-01
**Taak:** review vóór commit van de gestagede diff voor issue #42 (bladeren in het log, link "Meer in het log").

## Wat ging goed
De opdracht noemde de verwachte waarden, de norm en de testcommando's. Daardoor kon ik direct toetsen. De unitsuite (342 geslaagd) en ruff (alleen de bekende fout buiten de diff) draaiden zonder gedoe.

## Wat kon beter
Mijn eerste mutantrun gebruikte `-k "log"`. Die selectie miste de test voor ongeldige pagina's, omdat die naam geen "log" bevat. Twee mutanten leken daardoor te overleven.

## Wat deed je zelf goed
Ik controleerde de uitkomst van "overleefd" voordat ik die meldde, en draaide de mutanten opnieuw tegen het hele testbestand. Zo bleef één echte overlever over: de drempel van de link onder een overzicht.

## Wat heb je onderweg verbeterd
Mutanten draai ik nu tegen het hele testbestand, niet tegen een selectie op naam.

## Wat kan structureel beter
Zet in de opdracht: draai een mutant tegen het hele testbestand van de wijziging, niet met een `-k`-selectie op naam.
