# Terugblik aegis, review #452 (wachttijd in UTC)

Datum: 2026-11-28. Taak: securityreview vóór de commit van #452, de wachttijd van de integratie na een fout rond de overgang naar wintertijd.

## Wat ging goed

De opdracht noemde de drie dingen die niet mochten veranderen: de wachttijd na een fout, het onderscheid nieuw token of verzoek van een beheerder, en de telling van de 404 van Traefik. Daardoor kon ik gericht lezen. De diff was klein en `fout_op` wordt op vier plekken gebruikt, die ik met één grep vond.

## Wat kon beter

De opdracht noemde geen Python-versie. `datetime.UTC` bestaat pas sinds Python 3.11, dus ik zocht de versie zelf op (`requires-python >=3.13`, image `python:3.14-slim`).

## Wat deed je zelf goed

Ik heb de semantiek van `fold` met een losse python3-aanroep nagerekend, buiten de testmap. Die laat zien dat 02:30 met fold 0 en fold 1 in dezelfde tijdzone 0 minuten uiteen liggen en na de fix 60 minuten. Ik heb ook nagegaan dat de nieuwe test vóór de fix faalt: zonder de fix blijft `wachten` waar en volgt alleen de GET op `/leden/importverzoek`.

## Wat heb je onderweg zelf verbeterd

Bij het narekenen bleek dat een tijdstip in het dubbele uur nooit gelijk is aan hetzelfde tijdstip in UTC (PEP 495). Ik heb daarom gecontroleerd of een test `fout_op` met `==` vergelijkt. Dat doen regels 326 en 353 van `tests/unit/test_integratie.py`, maar met `OCHTEND` (31 oktober, 10:00), dus buiten het dubbele uur. De logica zelf trekt alleen af.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: noem bij een review van tijd- of datumcode de Python-versie van het geraakte onderdeel (pyproject en Dockerfile), en of tijdstippen in de code altijd een tijdzone hebben.
