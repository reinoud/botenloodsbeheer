# Terugblik sentinel, review issue #34 (screenshotscript)

Datum: 2026-11-05. Taak: review van de gestagede diff voor issue #34 (QR-vak, imagenaam, datumnotatie).

## Wat ging goed
De brief noemde de keuzes van de regie, het proefcommando en de plek van de proefscripts. Daardoor kon ik de bewering over `LANGUAGE` in vijf minuten zelf herhalen met een eigen proef, zonder het script te draaien.

## Wat kon beter
De brief zei niet dat er van eerdere runs nog een image `botenloods-doc-e2e` op de host staat. Dat vond ik pas met `docker image ls`.

## Wat deed ik zelf goed
Ik heb de bewering over de datumnotatie onafhankelijk getoetst (headless shell gaf 04/01/2025, volledige Chromium met `LANGUAGE=nl_NL` gaf 01-04-2025) en met `grep` in de templates nagegaan dat alleen `boot.html` een datumveld heeft, zodat geen teruggezette afbeelding nog de Amerikaanse notatie toont.

## Wat heb ik onderweg verbeterd
In plaats van alleen de compose-bestanden te lezen heb ik `docker compose config` gerenderd, om te zien dat `build` en `image` samen in de dienst e2e staan.

## Wat kan structureel beter
Zet in de opdracht: "Verandert een wijziging de naam van een image, noem dan in de brief of het oude image nog op de host staat en wie het opruimt."
