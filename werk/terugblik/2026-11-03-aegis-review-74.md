# Terugblik aegis, review #74 (en #73, Dockerfile)

Datum: 2026-11-03
Taak: securityreview van de gestagede diff vóór commit. Oordeel: akkoord.

## Wat ging goed

De brief noemde per bronsoort het verwachte gedrag (NUL in JSON: ongeldig en 200; te groot getal: standaardwaarde en melding). Daardoor kon ik gericht toetsen of een standaardwaarde ergens gevaarlijk wordt, in plaats van te zoeken naar wat de bedoeling was.

## Wat kon beter

Het acceptatiecriterium in #74 noemt nog 422. De afwijking volgt de bestaande documentatie, maar staat nergens in het issue zelf. Een lezer van het issue ziet een niet-gehaald criterium.

## Wat deed ik zelf goed

Elke route met `type=getal` nagelopen tot in de domeinfunctie: `eigenaar` valt niet terug op club, `_soorten` negeert onbekende id's al en weigert een lege lijst, `kaartjes` filtert in Python, `toewijzen` weigert `None`. De Werkzeug-bron in de container gelezen in plaats van het gedrag van `get` en `getlist` aan te nemen. De draaiende `web` en `api` gecontroleerd op het nieuwe commando en op de afwezigheid van de control-server-melding.

## Wat heb ik onderweg verbeterd

Een ImportError in de log van `api` (16:24:05) eerst als mogelijk circulaire import gezien. Na controle bleek het de reloader halverwege de bewerking; de herstart om 16:24:08 is gezond en de tests slagen.

## Wat kan structureel beter

Zet in de opdracht: wijkt de bouw bewust af van een acceptatiecriterium in het issue, pas dan vóór de review het criterium in het issue aan en verwijs naar de bron die voorgaat.
