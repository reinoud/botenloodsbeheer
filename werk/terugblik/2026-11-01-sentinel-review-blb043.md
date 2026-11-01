# Terugblik: review BLB-043 (twee logs)

Datum: 2026-11-01. Taak: review van de gestagede diff voor issue #37.

## Wat ging goed

De opdracht noemde de bewuste keuzes van de regie apart. Daardoor hoefde ik `plaats.gewijzigd` onder het plaatsdetail en het ontbreken van `boot.gewijzigd` niet als bevinding te wegen. De overlay gaf het commando voor een mutant met een bind mount; drie mutanten draaiden zonder de stack te raken.

## Wat kon beter

`tests/e2e/draai.sh` herstart de integratiecontainer en schrijft `secrets/api_token`, ook bij één test met `-k`. Dat raakt de gedeelde stack. De opdracht vroeg om die aanroep, maar noemde dat bijeffect niet.

## Wat deed ik zelf goed

Ik koos de mutanten op de drie eisen van het criterium: een soort in geen log, een soort in beide logs, en een overzicht dat technische regels doorlaat. Alle drie faalden in de suite. Vóór de testrun controleerde ik met `git diff --stat` dat alleen de overlay ongestaged was.

## Wat heb ik onderweg zelf verbeterd

Ik zag dat `web` al 21 uur draaide en controleerde in `compose.dev.yml` dat `app` gemount is met `--reload`, zodat de E2E-test de gestagede code toetst en niet een oud image.

## Wat kan structureel beter

Zet in de opdracht: "`tests/e2e/draai.sh` herstart de integratiecontainer en vervangt `secrets/api_token`; meld het aan de andere agents als die de stack tegelijk gebruiken."
