# Terugblik: herreview slice 12 (issue #80)

**Datum:** 2026-11-04
**Taak:** herreview van de gestagede diff van slice 12, Sentinel

## Wat ging goed

De mutanten en het commando van de vorige review stonden klaar in de scratchpad. Daardoor kon ik mutant s2 direct opnieuw draaien. Ik controleerde eerst met `diff` dat de mutant op één regel na gelijk is aan de gestagede `app/domein/indeling.py`.

## Wat kon beter

De opdracht kwam om 02:45 binnen, in het nachtvenster van #45. De E2E-run moest daardoor met de omweg. Voor de aanroep van `leden.import_aanvragen` moest ik zelf de actor (`app.domein.CLI`) opzoeken.

## Wat deed ik zelf goed

Ik bekeek het logo in alle zeventien gestagede afbeeldingen met een script. Het script vergelijkt de hoek met het logo met die van `openbaar.png`. Daarnaast bekeek ik de schermen met namen zelf. `rek-wijzigen.png` wijkt alleen af omdat het een uitsnede zonder kopbalk is; die heb ik ook bekeken.

## Wat heb ik onderweg verbeterd

Ik gebruikte een eigen testdatabase (`botenloods_sentinel12h`) met een conftest die ik vers uit de index afleidde, en niet de conftest van de vorige reviewer. Die kon verouderd zijn.

## Wat kan structureel beter

Zet in de opdracht: "Valt de E2E-run in het nachtvenster, voer de omweg dan uit met `docker compose -f docker-compose.yml -f compose.dev.yml exec -T web python -c 'from app import create_app; from app.domein import CLI, leden; app=create_app(); app.app_context().push(); leden.import_aanvragen(CLI)'`."
