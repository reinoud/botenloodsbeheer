# Terugblik sentinel, review #428

Datum: 2026-11-25
Taak: review vóór commit van #428 (menu markeert de kop op vijf pagina's na een formulier), branch `fix/428-menu-kop`.

## Wat ging goed

De brief noemde de mutanten die de regie al had gedraaid. Daardoor kon ik gericht twee andere endpoints kiezen (`web.kaartjes_print` en `web.beheerder_herstellen`). De uitbreiding met `beheerder_herstellen` stond er met reden bij, zodat ik die niet als scope creep hoefde te onderzoeken.

## Wat kon beter

De brief noemde de unitsuite zonder `--no-deps` in de tekst over de mutant, wel in het commando voor de suite. Ik heb het commando van de suite aangehouden. Het testbestand heeft drie lege regels vóór de nieuwe test en één erna; ruff meldt dat niet, het is alleen opmaak.

## Wat deed ik zelf goed

Ik heb de mutanten als bind mount van alleen `base.html` gedraaid, gecontroleerd met een diff tegen de gestagede versie, en per mutant de falende assert genoemd (`tests/unit/test_blok3b_detail.py:78`). Vóór de runs heb ik met `git diff --stat` vastgesteld dat er geen niet-gestagede wijzigingen in de gemounte paden waren.

## Wat heb ik onderweg verbeterd

In plaats van een map met een kopie van heel `app` heb ik alleen het template gemount, volgens de overlayregel voor templatemutanten. Dat is kleiner en raakt niets anders.

## Wat kan structureel beter in de opdracht

Zet in de opdracht: een mutant op een template draait als bind mount van alleen dat template (`-v <scratchpad>/base.html:/app/app/web/templates/base.html:ro`), niet als kopie van heel `app`.
