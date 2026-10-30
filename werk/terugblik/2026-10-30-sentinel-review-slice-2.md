# Terugblik sentinel: review slice 2

**Datum:** 2026-10-30
**Taak:** review vóór de commit van slice 2 (issue #11, met #2 en #10)

## Wat ging goed

De opdracht noemde de normwaarden (10 minuten, 5 pogingen, 15 minuten, 12 uur), de verschoven criteria en de commando's. Daardoor kon ik direct tegen een norm toetsen. Unit (178 geslaagd) en E2E (10 geslaagd, 1 los met `-k`) liepen zonder herhaling.

## Wat kon beter

BLB-003 criterium 1 ("staat niet meer bij de vrije plaatsen") hangt ook af van BLB-015, net als BLB-011 criterium 2. Issue #11 noemt alleen dat laatste als verschoven. Ik moest dat zelf afleiden.

## Wat deed ik zelf goed

Ik heb de racehelper gelezen in plaats van de mutantclaim van forge over te nemen. De helper eist dat de tweede sessie na een seconde nog wacht. Een gewone SELECT wacht in PostgreSQL niet, dus de test valt zonder `FOR UPDATE` om.

## Wat heb ik onderweg verbeterd

Ik heb de unitsuite gestart terwijl ik de diff las, en de E2E-suite terwijl ik de tests las. Zo bleef de wachttijd van de E2E-suite (pauze van 40 seconden per bestand) buiten het leeswerk.

## Wat kan structureel beter

Zet in de opdracht: "Noem bij elk verschoven criterium ook de criteria die van dezelfde latere story afhangen, zodat de reviewer ze niet zelf hoeft te zoeken."
