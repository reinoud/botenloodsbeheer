# Terugblik: review test grens "Meer in het log" (issue #42, ronde 2)

Datum: 2026-11-01. Taak: review van de gestagede test in `tests/unit/test_web_beheer.py` en mutant `>= 1` draaien.

## Wat ging goed
De opdracht gaf het exacte mountcommando, de scratchpad en de grens. De review paste in twee aanroepen.

## Wat kon beter
De opdracht noemde niet welke test de bovenkant van de grens (50 regels, link wel) dekt; dat moest ik uit de bestaande tests afleiden.

## Wat deed ik zelf goed
Eerst `git diff --stat` gecontroleerd (leeg), en met `grep -c` bevestigd dat de mutant echt in het gemounte bestand stond voordat ik de run telde.

## Wat heb ik onderweg verbeterd
Beide runs in één aanroep gedraaid, zodat het aantal tests (38) met en zonder mutant direct vergelijkbaar was.

## Wat kan structureel beter
Zet in de opdracht: "Noem bij een grenstest beide kanten van de grens met de testnaam die elke kant dekt."
