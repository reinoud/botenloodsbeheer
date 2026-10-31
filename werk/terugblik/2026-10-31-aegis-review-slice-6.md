# Terugblik aegis, securityreview slice 6

Datum: 2026-10-31
Taak: securityreview van de gestagede diff van slice 6 (integratiecontainer, import via de API).

## Wat ging goed

De brief noemde de toetsbasis, de verwachte waarden en het netwerk voor de positieve controle. Daardoor kon ik gericht toetsen: hetzelfde token gaf 200 vanaf `koppeling` en 401 vanaf `achterkant`, dus de whitelist werkt echt.

## Wat kon beter

De proef op de rate limit in een losse nginx-container heb ik niet gedaan. De regels voor `limit_req` zijn in deze diff niet gewijzigd, dus het risico is klein, maar de brief vroeg erom.

## Wat deed ik zelf goed

Ik heb de CSRF-vrijstelling positief gecontroleerd met een PUT en een POST via Nginx die 422 gaven zonder wijziging in de database, in plaats van een import met effect op de gedeelde database. Ik heb ook vanuit de netwerken van de integratiecontainer gecontroleerd dat `db`, `api` en `web` niet bereikbaar zijn.

## Wat heb ik onderweg zelf verbeterd

Eerst wilde ik een eigen token aanmaken voor de proef. Ik heb in plaats daarvan het bestaande secretbestand alleen-lezen gemount, zonder de waarde te tonen. Zo kwam er geen schrijfactie in de gedeelde database.

## Wat kan structureel beter

Zet in de opdracht: "Geef de reviewer een tweede token zonder `leden:importeren` mee (of zeg dat hij er een mag maken), zodat hij de 403 op nieuwe API-routes via Nginx kan controleren."
