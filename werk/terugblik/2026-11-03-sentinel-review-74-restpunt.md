# Terugblik Sentinel, review restpunt #74 (mutanten beheer.py:108, :140, :172)

Datum: 2026-11-03. Taak: review van de gestagede testwijziging in tests/unit/test_web_beheer.py.

## Wat ging goed
Mutanten en commando lagen klaar; drie runs en de controlerun kostten één aanroep.

## Wat kon beter
De opdracht zei niet dat de testcontainer de werkmap leest. Hier was dat gelijk aan de gestagede stand (bestand alleen gestaged), maar dat moest ik zelf nagaan.

## Wat deed ik zelf goed
Per mutant eerst de diff met het origineel bekeken, zodat vaststond dat elke mutant precies één regel raakt.

## Wat heb ik onderweg verbeterd
Uitvoer gefilterd op FAILED en de fout, zodat het antwoord kort blijft.

## Wat kan structureel beter
Zet in de opdracht: "De testcontainer leest de werkmap; meld of het te toetsen bestand niet-gestagede wijzigingen heeft."
