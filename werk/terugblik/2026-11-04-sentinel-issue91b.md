# Terugblik sentinel, herreview issue #91

Datum: 2026-11-04. Taak: review van de gestagede diff voor #91 (413 via Traefik in plaats van 502), tweede ronde.

## Wat ging goed

De brief noemde de vorige afkeuring, de mutant die de regie al had gedraaid, de grens van 50 verzoeken per adres en dat ik de enige was die suites draaide. Daardoor kon ik direct gericht proeven, zonder overleg met andere agents.

## Wat kon beter

De brief noemde niet het tijdstip van de laatste herlaadbeurt van `api`. Ik heb in de log zelf nagezocht dat de laatste herlaadbeurt (17:57) vóór mijn runs lag.

## Wat deed je zelf goed

Voor de proef via Traefik was geen echt token nodig: de 413, 404 en 405 ontstaan vóór de tokencontrole. Met een willekeurige Authorization-kop per verzoek kreeg elk verzoek een eigen emmer, en er hoefde geen token gemaakt en ingetrokken te worden. Per verzoek dat de app bereikte, stond er precies één regel in de log van `api` (18 van 18).

## Wat heb je onderweg verbeterd

Mijn eerste proef op `web` gaf 400, omdat `http.client` zelf al een Host-kop zette naast de mijne. Met `skip_host=True` kwam de verwachte 413 van Traefik.

## Wat kan structureel beter

Zet in de opdracht: "Een proef via de proxy met `http.client` gebruikt `putrequest(..., skip_host=True)` als de Host-kop zelf gezet wordt; anders geeft Traefik 400."
