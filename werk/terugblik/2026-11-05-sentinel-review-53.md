# Terugblik sentinel, review issue #53

**Datum:** 2026-11-05
**Taak:** review vóór de commit van `tests/proxy/` (proef van de API van buiten met een losse Traefik), met runs en mutanten

## Wat ging goed

Het script was twee keer achter elkaar groen, in 62 en 66 seconden. Elke run ruimde containers, volume en netwerken op, ook de run die halverwege afbrak. De brief noemde de mutantroute per soort bestand (`EXTERN_BESTAND` voor labels, een kopie van de map voor de rest). Daardoor kon ik zonder vragen beginnen.

## Wat kon beter

Een kopie van alleen `tests/proxy` werkt niet: het script springt naar `../..` en heeft daar `docker-compose.yml`, `compose.api-extern.yml` en de bind mounts `docker/db-init.sh`, `huisstijl` en `secrets/api_token` nodig. Mijn eerste mutantrun faalde op het wachtwoord van de database, omdat Docker voor het ontbrekende `db-init.sh` een lege map aanmaakte. Dat kostte twee runs van ongeveer een minuut.

## Wat deed ik zelf goed

Naast de gevraagde mutanten heb ik een mutant op de Traefik zelf gedraaid (`forwardedheaders.insecure=true` op `websecure`). Die bleef groen. Dat klopt met het ontwerp, want de applicatie neemt met `PROXY_HOPS=1` het laatste adres. Het laat wel zien dat het script het gedrag toetst en niet elke eis aan Traefik.

## Wat heb ik onderweg zelf verbeterd

De mislukte mutantrun heb ik als bewijs gebruikt voor het foutpad van `robot()` in een toewijzing: het script meldde "Token proxytest-a aanmaken mislukt", stopte met exitcode 1 en liet niets achter. Daarna heb ik de kopie aangevuld en de mutant opnieuw gedraaid.

## Wat kan structureel beter

Zet in de opdracht: "Een mutant op `tests/proxy/klant.py` of `compose.traefik.yml` draait in een kopie met deze opbouw: `docker-compose.yml`, `compose.api-extern.yml`, `docker/db-init.sh`, een lege map `huisstijl`, een leeg bestand `secrets/api_token` en `tests/proxy/`; alles uit de index (`git show :pad`)."
