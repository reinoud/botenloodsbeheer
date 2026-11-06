# Terugblik sentinel, derde review issue #157

Datum: 2026-11-06. Taak: review van de gestagede diff voor issue #157, met nadruk op het herstel van de lege cel `bootsoorten` en de stuurtekens.

## Wat ging goed

De brief noemde het herstel precies: wanneer een lege cel mag, welke tekst de weigering geeft en welke functies stuurtekens weigeren. Daardoor kon ik de code regel voor regel tegen het besluit leggen. Het herstel zelf klopt: `_controleer` weigert een lege cel bij een bestaande plaats met bootsoorten met `GEEN_SOORT`, en de tests vangen beide kanten (de rondgang met een lege plaats, de vrije en de bezette plaats met bootsoorten).

## Wat kon beter

De uitleg in het sjabloon is niet meegegaan met het herstel. ADR en handleiding zeggen "alleen bij een nieuwe plaats of een plaats die al geen bootsoort heeft"; het sjabloon zegt alleen "niet bij een plaats met een boot". Het herstel raakte drie teksten, en er is er één vergeten.

## Wat deed ik zelf goed

Ik heb de drie teksten (sjabloon, ADR, handleiding) naast elkaar gelegd in plaats van alleen de code te toetsen. Ook heb ik de aanroepers van de nieuwe kernen en `_flush_rek` nagelopen, zodat de verplaatste rollback geen pad zonder rollback achterlaat.

## Wat heb ik onderweg verbeterd

Ik wilde eerst de parser met een los script nalopen. Dat was niet nodig: de vorige review had dat al gedaan en de wijziging in de parser is niet veranderd. Ik heb de tijd besteed aan de teksten.

## Wat kan structureel beter

Zet in de opdracht: "Verandert een herstel een regel die ook in een gebruikerstekst staat (sjabloon, handleiding, ADR, schermuitleg), noem dan alle plaatsen van die tekst met bestand:regel, en werk ze in dezelfde ronde bij."
