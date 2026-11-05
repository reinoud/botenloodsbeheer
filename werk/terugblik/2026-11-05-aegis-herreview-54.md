# Terugblik aegis, herreview issue #54

**Datum:** 2026-11-05
**Taak:** securityreview van de gestagede diff op `fix/54-proxyprotocol` na herstel van AEG-01 en AEG-02.

## Wat ging goed

De brief noemde de herstelde punten met bestanden, de routers naar `api`, het besluit over `X-Forwarded-For` en de log van de regie. Daardoor kon ik zonder eigen testrun toetsen: de log toont per controle de PROXY-kop, de code en de laag die antwoordt.

## Wat kon beter

De brief noemde niet dat `docs/PROJECT-OVERLAY.md` ook niet-gestagede wijzigingen heeft. Ik zag het zelf in `git status`. Voor deze review maakte het niet uit.

## Wat deed je zelf goed

Ik heb de negatieve proeven getoetst op hun positieve tegenhanger: een PROXY-kop van buiten `trustedips` met het adres van `toegestaan` zou 200 geven als Traefik de kop vertrouwde; de proef verwacht 401 en 403 van de juiste laag. Zo is de 401 geen toevallige weigering.

## Wat heb je onderweg verbeterd

Ik heb nagegaan waarom de proef op `%2F` een 400 van de applicatie toont in plaats van Traefik: de test-Traefik zet `encodedcharacters` niet, en ADR-013 noemt beide lagen. Dat is bestaand gedrag en geen bevinding.

## Wat kan structureel beter

Zet in de opdracht: noem in een reviewbrief de niet-gestagede bestanden in de werkmap (`git status --short`, regels met een tweede kolom) en of de review ze negeert.
