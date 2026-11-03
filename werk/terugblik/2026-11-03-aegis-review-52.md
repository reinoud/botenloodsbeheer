# Terugblik aegis, securityreview issue #52

Datum: 2026-11-03. Taak: securityreview van de gestagede diff voor #52 (`leden:importeren` alleen via de CLI).

## Wat ging goed
De opdracht noemde de controleplek (domeinlaag, `actor.soort`) en de twee webroutes. Daardoor was de toets snel rond: alle webingangen lopen via `uitvoeren` met `Actor.van`, dus via dezelfde controle.

## Wat kon beter
Ik heb geen mutant of live proef gedraaid, omdat sentinel tegelijk op dezelfde database werkt en de domeincontrole statisch eenduidig is. Een dynamische positieve controle ontbreekt daardoor in mijn review.

## Wat deed je zelf goed
De documentatiezin naast beide compose-bestanden gelegd en gezien dat `iprem` ook op de interne router zit, niet alleen op de externe.

## Wat heb je onderweg verbeterd
Mijn eerste lezing van de zin over de load balancer als fout bijgesteld: hij volgt hetzelfde patroon als `installatie.md` en klopt; het punt is alleen een aanvulling.

## Wat kan structureel beter in de opdracht
Zet in de opdracht: "Draait sentinel parallel op dezelfde database, zeg dan of aegis een mutant van één testbestand mag draaien, of dat sentinel de mutant draait."
