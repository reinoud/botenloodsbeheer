# Terugblik sentinel, review issue #65 gecodeerd pad

Datum: 2026-11-03. Taak: review van de gestagede diff voor issue #65 (ADR-013 v1.3.0, BLB-022).

## Wat ging goed

- Brief met norm, verwacht gedrag en de proef van de bouwer: de toetsing kon direct beginnen.
- Geen niet-gestagede wijzigingen, en de testcontainer mount `app` en `tests`, dus suite en mutant draaiden op de gestagede code.

## Wat kon beter

- De brief verwachtte via de proxy een regel per verzoek in de log van `web`. De lokale Traefik heeft nu zelf de opties voor gecodeerde tekens en geeft de 400 voordat `web` het verzoek ziet. Via de proxy toont de lokale stack dus alleen de Traefik-laag.

## Wat deed je zelf goed

- De applicatielaag apart bewezen door Gunicorn in `web` en `api` direct aan te spreken (met `RAW_URI` zoals in productie), zonder de bucket te raken.
- De mutant geeft per test de falende waarde (302 of 404 in plaats van 400), niet alleen een aantal.

## Wat heb je onderweg zelf verbeterd

- Na de proxyproef zonder logregels in `web` eerst de argumenten van de draaiende Traefik gecontroleerd, in plaats van een fout in de app aan te nemen.

## Wat kan structureel beter in de opdracht of de afspraken

- Zet in de opdracht: noem per proef via de proxy welke laag in de lokale stack de 400 geeft; heeft de lokale Traefik de weigering zelf, laat de reviewer de applicatielaag dan direct op Gunicorn in de container proeven.
