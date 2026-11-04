# Terugblik sentinel, herreview MPO (issue #70)

**Datum:** 2026-11-04
**Taak:** herreview van de gestagede diff voor issue #70, met nadruk op de testwijziging (`ids=`, assert op het bronformaat).

## Wat ging goed

De brief noemde het commando voor de testrun en de mutant, en de scratchpadmap. Daardoor kon ik direct draaien en hoefde ik niets te zoeken.

## Wat kon beter

De brief meldde niet dat `docs/PROJECT-OVERLAY.md` een niet-gestagede wijziging heeft. Die raakt de test niet, maar ik moest dat zelf vaststellen.

## Wat deed je zelf goed

Eerst met `cmp` gecontroleerd dat de werkmap gelijk is aan de gestagede versie van beide gemounte bestanden, en de falende regel van de mutant genoemd in plaats van alleen het aantal.

## Wat heb je onderweg verbeterd

`commando.txt` naast de mutant gezet, zoals de overlay vraagt.

## Wat kan structureel beter

Zet in de opdracht: "Noem de niet-gestagede bestanden in de werkmap en of de review ze moet negeren."
