# Terugblik: herreview tijdstiptest slice 9

Datum: 2026-11-03
Taak: herreview van de testregel voor het tijdstip van de opschoning (BLB-026 criterium 5, issue #48)

## Wat ging goed

De opdracht noemde de mutant, het testbestand, de regel en de exacte commando's. Daardoor kostte de herreview vijf minuten. Mutant h3 faalt op precies de nieuwe regel (`assert (None is not None)`), niet op een bijvangst.

## Wat kon beter

De HTML-helft van de regel is een negatieve toets: de tekst "Laatste opschoning: nog niet" ontbreekt. Ze toetst niet dat het juiste tijdstip in de pagina staat. Voor dit criterium is dat genoeg, omdat JSON en HTML uit dezelfde gegevens komen, maar een verwisseling met een ander tijdstip valt er niet mee op.

## Wat deed je zelf goed

Eerst `git diff --stat` op `app/` en `tests/` gecontroleerd (leeg), daarna in de uitvoer nagegaan welke assert de mutant vangt, in plaats van alleen de telling over te nemen.

## Wat heb je onderweg verbeterd

De unitsuite gedraaid met `-rs`, zodat overgeslagen tests met reden in de uitvoer zouden staan. Er waren er geen.

## Wat kan structureel beter

Zet in de opdracht: "Een mutant telt pas als gevangen wanneer de reviewer de falende assert noemt, niet alleen het aantal mislukte tests."
