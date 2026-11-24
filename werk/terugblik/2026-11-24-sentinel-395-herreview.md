# Terugblik sentinel, herreview #395 (Leden: lijstfilter zonder knop)

Datum: 2026-11-24
Taak: herreview van de gestagede diff op `feature/leden-lijstfilter`, na de afkeuring op `tests/e2e/test_status.py:83` en het advies over het importblok.

## Wat ging goed

De brief noemde de twee punten uit de eerste review, de mutant en de commando's. Daardoor kon ik het herstel direct toetsen. De mutant (`</div>` van het lijstdeel na het importblok) liet alleen het geval `/leden` falen, met de verwachte melding op regel 83. De andere drie gevallen bleven groen.

## Wat kon beter

De brief vroeg om elk E2E-bestand met `main >` te draaien als er een omhullende `div` bijkomt. Zes bestanden gebruiken nog `main >`, maar geen daarvan op `/leden` (ze gaan over `/opgezegd`, Gaan opzeggen, zoeken en boten). Draaien was dus niet nodig; dat moest ik eerst per regel nagaan.

## Wat deed ik zelf goed

Ik heb vóór de E2E-run de stroom, het deksel en de compose-bestanden van `web` gecontroleerd, en de mutant in een kopie in mijn scratchpad gedraaid, met een diff als bewijs dat alleen de sluittag verschoof.

## Wat heb ik onderweg verbeterd

Mijn eerste grep combineerde twee patronen en gaf niets terug. Ik heb hem opnieuw gedraaid met alleen `main >` en de treffers per pagina nagelopen, in plaats van op de lege uitkomst te vertrouwen.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: noem bij de grep op `main >` ook het scherm, met `grep -rn 'main >' tests/e2e/ ` en de `goto` erboven, zodat de reviewer alleen de bestanden op het geraakte scherm draait.
