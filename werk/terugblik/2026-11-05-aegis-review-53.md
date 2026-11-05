# Terugblik aegis, review issue #53

**Datum:** 2026-11-05
**Taak:** statische securityreview van de gestagede proxyproef (`tests/proxy/`), issue #53

## Wat ging goed

De brief noemde de ADR-regels, de bekende open punten en waar de uitvoer van eerdere runs stond. Daardoor kon ik de mutantrun (403 werd 401) als bewijs gebruiken zonder de stack zelf te starten, en botste ik niet met de run van sentinel.

## Wat kon beter

De brief vroeg of de `%2F`-proef bij dit issue hoort, maar noemde de overlayregel (§4, regel 203) niet die zo'n proef bij elke proef op een rate limit vraagt. Die regel vond ik pas bij het lezen van de hele sectie.

## Wat deed ik zelf goed

De optienamen heb ik in `traefik:v3.7.17` op de digest uit de compose nagekeken met `--help`, dus niet uit mijn geheugen. Daarbij zag ik dat `underscoreheadersstrategy` verouderd is en niet wordt gebruikt. Ik heb ook nagelopen of een stille geslaagde run mogelijk is: dezelfde token geeft eerst 200 (positieve controle), de 404 krijgt eerst een controle op intern, en de controle op de config draait ook positief.

## Wat heb ik onderweg zelf verbeterd

Eerst wilde ik de grove `herkomst` (alles wat geen JSON is, telt als Traefik) als echt risico melden. Dat heb ik afgezwakt tot Info, omdat `web` niet in de stack draait en elke fout van de API JSON geeft.

## Wat kan structureel beter

Zet in de opdracht: "Noem de overlayregels uit §4 die op de proef van toepassing zijn bij nummer (zoals regel 203 over `%2F`), en zeg per regel of de proef er in dit issue aan moet voldoen of dat het een restpunt mag worden."
