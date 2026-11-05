# Terugblik Sentinel, review issue #31

Datum: 2026-11-05. Taak: review van de gestagede diff voor issue #31 (importslot, geen PUT per minuut). Oordeel: akkoord.

## Wat ging goed

De brief noemde de ontwerpkeuze, de plek van de API-tekst, het mutantcommando en de verwachte faalplek per mutant. Suite (726 passed, 0 skipped), ruff en vier mutanten draaiden zonder omweg.

## Wat kon beter

De brief zei dat mutant `slot = False` faalt op de assert na 60 minuten. Hij faalt op de assert na 59 minuten (`tests/unit/test_integratie.py:195`). Dat is ook de assert van het criterium, maar een reviewer die de brief letterlijk neemt, kan dit als afwijking lezen.

## Wat deed je zelf goed

Twee extra mutanten gedraaid: alleen de statuscode zonder de tekst (`slot = fout.code == 409`) en de logtekst weg. Beide vallen, op regel 183 en 187. Ook nagegaan dat de API-tekst zelf vastligt in `tests/unit/test_leden.py:314`, zodat de koppeling op tekst niet stil kan breken.

## Wat heb je onderweg verbeterd

Met `cmp` gecontroleerd dat de werkmap gelijk is aan de gestagede versie, voordat ik de mutanten van de gestagede versie afleidde.

## Wat kan structureel beter

Zet in de opdracht: noem per mutant de regel van de assert waarop hij faalt (bestand:regel), niet een omschrijving als "na 60 minuten".
