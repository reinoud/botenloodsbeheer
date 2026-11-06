# Terugblik Sentinel, 2026-11-06

Taak: review vóór commit van issue #130 (tests/proxy/draai.sh en tests/proxy/klant.py).

## Wat ging goed
De opdracht noemde de criteria, de proef en de logbestanden. De run van de regie (run-104852.log) liet per controle de codes en de herkomst zien, zodat ik de suite niet opnieuw hoefde te draaien.

## Wat kon beter
De nieuwe tempo-controle toetst bij de eerste tien aanroepen alleen de code (400), niet de herkomst. Een 400 van Traefik zou ook slagen. Het log laat zien dat de 400 van de applicatie komt, dus het risico is laag.

## Wat deed ik zelf goed
Ik heb de mutant uitgedacht in plaats van gedraaid: zonder rate limit geeft het pad twaalf keer 400 en geen 429, en dan faalt `tempo`. Dat scheelde een run van 100 s.

## Wat heb ik onderweg verbeterd
Ik heb de HTML-tak getoetst aan het log: elke 400 in de run is `400/applicatie` met JSON, de tak werd niet geraakt.

## Wat kan structureel beter
Zet in de opdracht: "Een controle op een reeks statuscodes toetst ook de herkomst van elke code, niet alleen de code."
