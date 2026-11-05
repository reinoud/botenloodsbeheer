# Terugblik sentinel, review issue #110

Datum: 2026-11-05. Taak: review vóór commit van `feature/110-verdieping-onderaan` (verdieping 1 onderaan op Indeling).

## Wat ging goed

De brief gaf het mutantcommando, de E2E-testnaam en de stand van de stack. Daardoor kon ik direct draaien zonder te zoeken. De diff is klein en het raster is één macro, dus nieuw rek en rek wijzigen delen dezelfde lus.

## Wat kon beter

De brief zegt niet dat het raster een macro is. "Beide rasters" las ik eerst als twee lussen; pas in het template bleek dat er één lus is voor twee aanroepen.

## Wat deed ik zelf goed

Naast de twee mutanten van de regie draaide ik een derde mutant die alleen het raster van een bestaand rek niet omkeert (`verdiepingen if plaatsen else verdiepingen|reverse`). Die viel op de melding "raster rek X", zodat ook die tak van de test bewezen is. Elke E2E-run ging twee keer, met uitvoer in de scratchpad.

## Wat heb ik onderweg verbeterd

Ik controleerde dat de draaiende `web` het nieuwe template serveert voordat ik de E2E-uitkomst meetelde, en bekeek de twee nieuwe schermafbeeldingen.

## Wat kan structureel beter

Zet in de opdracht: "Wordt een lus in een Jinja-macro gewijzigd, noem dan elke aanroep van de macro en de mutant die alleen één aanroep raakt."
