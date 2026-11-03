# Terugblik sentinel: review slice 11 (issue #56)

Datum: 2026-11-03. Taak: review van de gestagede diff voor BLB-028, bootsoorten beheren.

## Wat ging goed

De terugblik van de bouwer noemde de mutanten met pad en commando. Daardoor kon ik de drie slotmutanten (m08, m09, m10) direct draaien en eerst met `diff` tegen de gestagede versie controleren dat ze alleen het slot weghalen.

## Wat kon beter

Criterium 3 noemt de kaartjes, maar kaartjes en de openbare pagina `/p/` tonen geen bootsoort. Dat zag ik pas toen mijn eigen controletest faalde op een aanname. Het criterium is daar niet toetsbaar.

## Wat deed ik zelf goed

De kans op een deadlock heb ik per functie nagelopen op volgorde en soort slot (soort, boot, plaats bij `boot_wijzigen`; plaats, soort bij `plaats_wijzigen`; alleen de soort bij hernoemen en verwijderen) in plaats van alleen op de racetests te vertrouwen.

## Wat heb ik onderweg verbeterd

`tests/` is in de testcontainer alleen-lezen, dus een extra testbestand ernaast mounten lukt niet. Ik heb het in `/scratch` gemount en `tests.unit.conftest` als plugin geladen (`-p tests.unit.conftest --rootdir=/app`).

## Wat kan structureel beter in de opdracht

Zet in de opdracht: "Een losse controletest van de reviewer mount je als map op `/scratch` en draai je met `-e PYTHONPATH=/app -p tests.unit.conftest --rootdir=/app`; `tests/` is alleen-lezen in de container."

Zet in de opdracht: "Noemt een criterium een scherm (zoals de kaartjes), controleer dan eerst of dat scherm het gegeven toont; zo niet, dan gaat het criterium terug naar apex."
