# Terugblik aegis: security-review Traefik (#29, #36)

**Datum:** 2026-10-31
**Taak:** security-review van de gestagede wijziging Traefik vervangt Nginx

## Wat ging goed

De opdracht noemde de normen, de drempels en de netwerknaam. De proeven van forge stonden in één bestand, zodat ik alleen de gaten hoefde na te lopen. De whitelist en `X-Forwarded-For` kon ik met een positieve controle toetsen: een container met `--ip 10.203.0.99` op `koppeling` kreeg 200, een ander adres met een vervalste kop 401.

## Wat kon beter

De proef "foto van 9 MB op /boten slaagt" van forge was één keer gedraaid. De routers `boten` en `web` hebben dezelfde prioriteit (even lange regel), en Traefik kiest daartussen per start willekeurig. Eén geslaagde proef bewees dus niets. Dat zag ik pas in een losse Traefik na vijf herstarts.

## Wat deed ik zelf goed

De rate-limitproeven (padvarianten als `/%69nloggen`, `//inloggen`, `/x/../inloggen`) deed ik in een eigen Traefik met een stub, niet op de gedeelde stack. Het testtoken heb ik na gebruik ingetrokken en de intrekking gecontroleerd; het token stond in geen enkele log.

## Wat heb ik onderweg zelf verbeterd

Mijn eerste proef op de routerkeuze gaf geen onderscheid, omdat mijn losse configuratie geen grens op de grootte had. Ik ben overgestapt op de toegangslog van twee aparte stubs, met herstarts tussen de aanroepen.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: een proef op routering in Traefik (welke router een pad krijgt) draait na minstens drie herstarts van Traefik, en twee routers die hetzelfde pad kunnen raken, krijgen een expliciete `priority`.
