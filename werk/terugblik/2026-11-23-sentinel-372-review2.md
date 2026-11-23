# Terugblik sentinel, tweede review #372

**Datum:** 2026-11-23
**Taak:** tweede review vóór de commit van #372 (404 van Traefik in de integratiecontainer)

## Wat ging goed
De brief noemde precies de vier herstelpunten, de testnamen en de map voor de mutanten. Daardoor bleef de review klein: diff lezen, twee mutanten, één suiterun.

## Wat kon beter
Punt 4 zei "de te lange nieuwe regels" zonder te zeggen welke grens geldt. De Python-regels blijven onder 100 tekens (ruff); de nieuwe opmerking in `docker-compose.yml` is 103 tekens, maar dat bestand kent geen grens en heeft al 30 langere regels.

## Wat deed je zelf goed
De mutanten zelf gemaakt met een script met een assert op precies één vindplaats, en ze los gedraaid op een tweede eigen `TEST_DB`, naast de suite op de eerste. Zo verstoorden ze elkaar niet.

## Wat heb je onderweg zelf verbeterd
Eerst gecontroleerd dat de werkmap gelijk is aan de gestagede stand (`git diff` leeg), omdat `compose.dev.yml` de werkmap mount en niet de index.

## Wat kan structureel beter
Zet in de opdracht: "Noem bij een punt over regellengte de grens en het bestandstype (ruff 100 voor Python; YAML en Markdown zonder grens)."
De eigen testdatabases `botenloods_test_s372b` en `botenloods_test_s372m` staan nog in de lokale database. Zet in de opdracht of de reviewer zijn eigen testdatabase na afloop weghaalt.
