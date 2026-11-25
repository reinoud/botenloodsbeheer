# Terugblik Sentinel, herreview #418 deel 2 (vangnet)

Datum: 2026-11-25. Taak: herreview van de vier herstelpunten op `feature/418-vangnet`, met unit, E2E (twee keer), een mutant op de nieuwe E2E-assert en een peiling per entrypoint.

## Wat ging goed

De brief noemde precies de vier punten en wat al akkoord was. Daardoor kon ik gericht meten. De unit (69 geslaagd, 0 overgeslagen) en de E2E (twee keer vier fasen) slaagden direct, en de stack stond daarna weer healthy zonder vangnetcontainer.

## Wat kon beter

De E2E-assert toetst één pad (`/api/v1/ik`) op het publieke entrypoint. Het criterium "het vangnet beantwoordt geen enkel verzoek" vraagt meer. Dat heb ik zelf breder gepeild, met 360 verzoeken (methoden, paden, een vreemde Host, en het entrypoint `intern`) met en zonder vangnet. De uitkomst was gelijk, maar die peiling zit niet in de suite.

## Wat deed ik zelf goed

Ik heb de peiling eerst met de mutant laten zien dat ze werkt: zonder de uitsluiting gaven 48 verzoeken op `/api/` ineens 503. Zonder die positieve controle had een gelijke uitkomst ook kunnen betekenen dat het vangnet niet geladen was. De gedocumenteerde opstelling (`vangnet/compose.yml` naast `.env`) heb ik nagebouwd in de scratchpad en met `docker compose config` gecontroleerd, ook het effect van `-p` naast `COMPOSE_PROJECT_NAME`.

## Wat heb ik onderweg zelf verbeterd

De peiling raakte de rem van de API (429 met `Retry-After: 1`). Die header lijkt op die van het vangnet. Ik heb daarom op het verschil tussen de twee runs getoetst en niet op de header alleen, en een pauze gezet vóór de mutant-E2E.

## Wat kan structureel beter

Zet in de opdracht: een test die bewijst dat een dienst "niets beantwoordt", vergelijkt een reeks verzoeken per entrypoint met en zonder die dienst, en toont met een mutant dat de vergelijking een verschil ziet.
