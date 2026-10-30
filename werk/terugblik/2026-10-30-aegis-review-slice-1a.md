# Terugblik Aegis: securityreview slice 1a

**Datum:** 2026-10-30
**Taak:** securityreview van de gestagede diff voor slice 1a (issue #1, BLB-022, BLB-024)

## Wat ging goed

De opdracht noemde de toetspunten en de drie afwijkingen van Forge. Daardoor kon ik gericht lezen. De draaiende stack maakte het mogelijk de headers, de rate limit en de databaserechten live te bevestigen in plaats van alleen uit de code af te leiden.

## Wat kon beter

ADR-001 stond niet op het pad dat ik eerst probeerde (`docs/architecture/adr/`). Het kostte een extra stap. De opdracht noemde geen verwachte waarde voor de rate limit, dus ik heb 30 per minuut met een burst van 20 als passend beoordeeld zonder norm uit de ADR.

## Wat deed ik zelf goed

Ik heb de rate limit getest met een onbekende gebruikersnaam, zodat geen account een mislukte poging kreeg en de tests van Sentinel niet geraakt werden. Ik heb de databaserechten in `information_schema` gecontroleerd en niet op de migratietekst vertrouwd.

## Wat heb ik onderweg verbeterd

Ik vermoedde eerst dat de uitnodigingscode alleen via de toegangslog kon lekken. Bij het nalopen van de Nginx-configuratie in de container bleek de foutlog naar stderr te gaan, met de requestregel erin. Dat heb ik als laag punt opgenomen.

## Wat kan structureel beter

Zet in de opdracht: "Noem de paden van de ADR's en de verwachte waarden voor drempels (rate limit, vergrendeling, sessieduur), zodat de reviewer toetst tegen een norm en niet tegen eigen inschatting."
