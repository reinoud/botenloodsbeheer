# Terugblik pipeline, issue #53 proxytest

**Datum:** 2026-11-05
**Taak:** herhaalbare proef van de API van buiten met een losse Traefik (`tests/proxy/`)

## Wat ging goed

De brief noemde alle bronnen, de vrije ruimte (eigen projectnaam, eigen subnetten) en de valkuilen uit eerdere proeven (`skip_host`, 50 verzoeken per adres). Daardoor slaagde de eerste volledige run meteen. Dat `voorkant` en `koppeling` in `docker-compose.yml` extern zijn met `INSTALLATIE` in de naam, maakte een eigen stack naast de dev-stack eenvoudig.

## Wat kon beter

De opdracht vroeg om "labels renderen met `docker compose config`", maar met de echte `api` als upstream rendert compose de labels zelf. Ik heb `config` alleen gebruikt voor de controle zonder `API_EXTERN_BRONNEN`. De woordgrens van 60 gold voor de alinea, terwijl de telregel ook kop, versie en wijzigingslog meetelt (61 in totaal, 44 voor de alinea).

## Wat deed ik zelf goed

Elke controle kijkt ook wie antwoordde: 200 en 401 moeten JSON van de applicatie zijn, 403 en 404 platte tekst van Traefik. De 404 zonder het bestand heeft een positieve controle via `intern`, zodat een api die nog start geen valse 404 geeft. Het token gaat via de omgeving naar de client en staat in geen log.

## Wat heb ik onderweg zelf verbeterd

De stubproef liet zien dat een mislukte `flask token robot` het script zonder melding liet stoppen (set -e in een toewijzing). `robot()` meldt nu zelf de fout. Een overbodige `bash -c`-constructie voor `WACHT` is vervangen door een tijdelijke variabele vóór de functie.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Een woordgrens voor een alinea telt alleen de alinea; kop, versieregel en wijzigingslog tellen apart."
Zet in de opdracht: "Een proef met de echte `api` als upstream gebruikt `botenloods-app` zoals het lokaal staat; zeg of het image eerst herbouwd moet worden."
