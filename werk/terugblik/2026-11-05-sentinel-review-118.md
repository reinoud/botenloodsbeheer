# Terugblik sentinel, review #118

Datum: 2026-11-05. Taak: review vóór commit van de controle `actor != CLI` in `app/domein/tokens.py` (issue #118).

## Wat ging goed
De diff was klein en de brief noemde de keuze van de regie, het commando voor de suite en de mutant. De suite gaf 732 geslaagd, 0 overgeslagen, 0 errors. Ruff vond niets in de twee bestanden.

## Wat kon beter
De mutant van de regie zette beide controles tegelijk terug. Volgens de overlay krijgt elke controle een eigen mutant. Met één mutant blijft onzichtbaar of elke controle apart gedekt is.

## Wat deed ik zelf goed
Ik heb twee losse mutanten gemaakt (`maken` en `rechten_wijzigen`) en per mutant de falende assert genoemd: regel 101 en regel 108 van `tests/unit/test_persoonlijke_tokens.py`. Ik heb gecontroleerd dat de CLI het object `CLI` doorgeeft (`app/cli.py:45`), zodat de vergelijking op gelijkheid klopt.

## Wat heb ik onderweg verbeterd
Ik heb met `cmp` vastgesteld dat de werkmap gelijk is aan de gestagede versie van `tokens.py` voordat ik de suite draaide.

## Wat kan structureel beter
Zet in de opdracht: lever bij een diff met meer controles per controle een eigen mutant aan, met de verwachte falende assert als bestand:regel.
