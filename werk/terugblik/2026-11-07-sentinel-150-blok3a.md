# Terugblik Sentinel, review blok 3 deel A (#150)

**Datum:** 2026-11-07
**Taak:** review vóór de commit van de lijsten 1B met zoeken en filters en het log 3B, met unitsuite, E2E en mutanten.

## Wat ging goed

De opdracht noemde de aanroepers, de macro en de mutanten bij naam. Daardoor kon ik gericht controleren in plaats van zoeken. De bouwer had per mutant een commentaar in de test gezet; elke mutant viel op de plek die het commentaar noemde.

## Wat kon beter

De opdracht vroeg te wachten zonder poll, maar een subagent eindigt zijn beurt als hij niets meer aanroept. Een monitor op het uitvoerbestand van de achtergrondtaak loste dat op. Het uitvoerbestand van `draai.sh` bevat geen totaal: de run bestaat uit losse pytest-aanroepen, dus het totaal moest ik optellen.

## Wat deed ik zelf goed

Mutanten als bind mount over één bestand in de testcontainer, elk een los commando met een eigen uitvoerbestand. Naast de vijf gevraagde mutanten één extra: zoeken op de wachtlijst weg. De unitsuite draaide vóór de E2E-run, de mutanten tegen de aparte testdatabase tijdens de E2E-run.

## Wat heb ik onderweg zelf verbeterd

De inner join op `Boot.lid` in `wachtlijst.lijsten` leek een gedragswijziging voor de aanroepers `beheer.py:264` en `uitlezen.py:60`. Ik heb nagegaan dat een clubboot niet op de wachtlijst kan (`wachtlijst.py:73`, `boten.py:113`), en heb het daarom niet als bevinding gemeld.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Draai je een achtergrondrun als subagent, wacht dan met een `until grep -q`-lus op een eindregel in het uitvoerbestand; tel het E2E-totaal uit de losse `passed`-regels van `draai.sh` met een script."
