# Terugblik sentinel: review MPO-foto's (issue #70)

**Datum:** 2026-11-04
**Taak:** review vóór commit van de gestagede diff voor issue #70 (MPO toestaan).

## Wat ging goed

De brief noemde de randgevallen (logo, decompressiebom, KeyError in Pillow 13) en de mutant die de regie al had gedraaid. Daardoor kon ik direct gericht proeven, zonder de hele suite te draaien.

## Wat kon beter

De test controleert niet zelf dat de bron als MPO opent. Dat het zo is, blijkt nu alleen uit de mutant van de regie. Ook mist `ids=`, terwijl de briefingchecklist dat vraagt bij binaire invoer; de ids zijn nu `JPEG-extra0` en `MPO-extra1`.

## Wat deed je zelf goed

Ik heb de KeyError met `formats=["MPO"]` in een vers proces gereproduceerd, zodat de keuze voor `formats=OPENEN` aantoonbaar nodig is. De randgevallen (logo als MPO, bom tussen 40 en 80 miljoen pixels, bom boven 80 miljoen, groot tweede beeld, EXIF-oriëntatie) staan in één proefscript in de scratchpad.

## Wat heb je onderweg verbeterd

Ik heb het groot tweede beeld als extra geval toegevoegd. Dat beeld wordt niet gedecodeerd, dus de grens op het eerste beeld is genoeg.

## Wat kan structureel beter

Zet in de opdracht: een test met een nieuwe bronvorm controleert eerst zelf dat de bron die vorm heeft (bijvoorbeeld `Image.open(bron).format == "MPO"`), zodat de test niet stil een ander geval test als de bibliotheek verandert.
