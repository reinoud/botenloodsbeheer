# Terugblik foundation: ADR-013 gecodeerd pad (issue #65)

**Datum:** 2026-11-03
**Taak:** ontwerpbesluit voor gecodeerde tekens in het pad vastleggen in ADR-013, met proef in een losse Traefik v3.7.17.

## Wat ging goed

De brief noemde de bronnen en welke leidend was, de lokale images, de scratchpadmap en de regels voor de proef. Daardoor kon ik direct een losse stack starten. `traefik --help` gaf de exacte namen van de opties voor gecodeerde tekens, zonder documentatie van buiten.

## Wat kon beter

Mijn eerste proef had een stub die alleen het pad terugstuurde. Die liet zien welke router een verzoek kreeg, maar niet welke paden Flask echt verwerkt. Pas met een kleine Flask-app achter Gunicorn bleek dat alleen `%2F` een inlog oplevert en de andere codes 404 geven. Ook kost de file provider een herstart van Traefik na een wijziging van het bestand.

## Wat deed ik zelf goed

Ik heb het voor de hand liggende eenregelige herstel (`url_map.merge_slashes = False`) eerst geprobeerd in plaats van het aan te nemen. Het werkt niet na het aanmaken van de `Map`; dat staat nu als verworpen alternatief in de ADR. Ik heb ook gecodeerde letters (`%69`) getest, een omzeiling die geen optie van Traefik dekt; Traefik decodeert die zelf.

## Wat heb ik onderweg zelf verbeterd

De stub vervangen door Flask achter Gunicorn, en een check op `RAW_URI` en `PATH_INFO` toegevoegd om te zien wat Gunicorn doorgeeft. De ADR-tekst na de eerste telling ingekort van 360 naar 313 woorden extra.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: een proef op routering in Traefik gebruikt als upstream een kleine Flask-app achter Gunicorn met dezelfde routes, niet alleen een stub die 200 geeft; zo is zichtbaar of de applicatie het verzoek ook verwerkt.
