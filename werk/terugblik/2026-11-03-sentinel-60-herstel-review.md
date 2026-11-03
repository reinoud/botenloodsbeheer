# Terugblik: herreview herstel test #60

Datum: 2026-11-03
Taak: herreview van het herstel in `tests/unit/test_migratie_en_taken.py` (issue #60, rechten `botenloods_taken`).

## Wat ging goed

De opdracht noemde het oude oordeel, de diff, de mutant en het commando. Daardoor kon ik direct draaien. De mutant verschilt maar op één regel van de migratie (`taakrun`: `DELETE, UPDATE`), dus de uitkomst is eenduidig.

## Wat kon beter

De opdracht noemde niet hoe de regie de mutant had gemount. Ik heb dat zelf afgeleid (`-v ...:ro` op `docker compose run`). Een kant-en-klaar commando scheelt een stap en voorkomt dat twee runs verschillend opgezet zijn.

## Wat deed je zelf goed

Ik controleerde eerst met `git diff --quiet -- app tests migrations` dat de werkmap gelijk is aan de index, en met een `diff` dat de mutant alleen die ene regel wijzigt. Ik koppelde de falende test aan regel 90, de tweede `taken.hartslag()`, en niet alleen aan de testnaam.

## Wat heb je onderweg zelf verbeterd

Ik draaide de volledige suite met `-rs`, zodat overgeslagen tests in de uitvoer zouden staan. Er waren er geen.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Geef bij een mutantrun het volledige commando mee, inclusief de bind mount, zodat regie en reviewer dezelfde run doen."
