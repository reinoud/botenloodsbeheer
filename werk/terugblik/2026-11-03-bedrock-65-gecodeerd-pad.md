# Terugblik bedrock, issue #65 gecodeerd pad

Datum: 2026-11-03. Taak: app-laag, entrypoints, documentatie en proef voor het gecodeerde pad (ADR-013 v1.3.0).

## Wat ging goed

- Brief met ADR-alinea, tabel en criterium: geen aannames nodig. `RAW_URI` zetten Gunicorn en de testclient allebei, dus geen andere bron nodig.
- De overlay-regels voor de proef (eigen projectnaam, Flask achter Gunicorn, drie herstarts) waren direct uitvoerbaar.

## Wat kon beter

- De losse proef kost veel tijd: een tweede volledige stack met vier varianten. Een script in de repository zou dat hergebruikbaar maken.
- Een 400 van Flask (CSRF), van de app-laag en van Traefik zijn aan de statuscode niet te scheiden. Ik moest op de logs van `web` letten.

## Wat deed je zelf goed

- Vier varianten (geen laag, alleen app, alleen Traefik, beide) met een mutant als bind mount, zodat elke laag apart bewezen is.
- Baseline zonder lagen toont 302, dus de proef bewijst iets.

## Wat heb je onderweg zelf verbeterd

- Een `--since` op de logs met UTC tegen lokale tijd gaf ruis; ik controleerde opnieuw met een korter venster en hercontroleerde of Traefik de 400 zelf gaf.

## Wat kan structureel beter in de opdracht of de afspraken

- Zet in de opdracht: bij een proef op een weigering noem welke laag de 400 moet geven en hoe de reviewer dat ziet (logregel in `web`, geen regel in `web`).
- Zet in de opdracht: de toegangslog maskeert alleen `/uitnodiging/...`; een pad met `%2F` ervoor toont de uitnodigingscode ongemaskeerd (restpunt, zie antwoord).
