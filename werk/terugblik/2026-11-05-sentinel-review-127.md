# Terugblik sentinel, review issue #127

Datum: 2026-11-05. Taak: review vóór de commit van `tests/proxy/draai.sh` en `tests/proxy/klant.py` (gecodeerd pad, herkomst, Retry-After).

## Wat ging goed
De brief noemde de leidende overlayregels (§4, regel 152 over de kopie, regel 228 over `draai.sh`) en wat de regie al had gedraaid. Daardoor kon ik een mutant kiezen die iets nieuws bewijst, in plaats van de run van de regie te herhalen.

## Wat kon beter
Mijn opruimcommando zat in dezelfde shellregel als de controle met `docker ps -a`. Het werd vastgehouden en de controle liep pas bij een tweede poging. Een kopie met een leeg `secrets/api_token` blijft in de scratchpad staan.

## Wat deed ik zelf goed
Ik combineerde de mutant op `herkomst` met de mutant zonder `externtoegang`. Zo is zichtbaar dat de strengere `herkomst` (klant.py:55-57) de controle op het gecodeerde pad laat falen: met de oude regel gaf de applicatie een 400 en slaagde die controle stil.

## Wat heb ik onderweg verbeterd
Mijn eerste vervanging in `compose.api-extern.yml` raakte twee plekken (de definitie en de verwijzing) en de assert hield hem tegen. Daarna heb ik alleen de verwijzing in `middlewares` vervangen en het resultaat met `diff` tegen de index gecontroleerd.

## Wat kan structureel beter
Zet in de opdracht: "Een mutant op een controlefunctie in `klant.py` draai je samen met een mutant op de labels die een antwoord van de applicatie oplevert; anders kan de mutant tegen een echte Traefik niet falen." Zet er ook in: "Opruimen en controleren zijn aparte commando's."
