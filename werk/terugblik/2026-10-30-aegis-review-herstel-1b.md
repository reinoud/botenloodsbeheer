# Terugblik Aegis: securityreview herstel slice 1b (#9)

Datum: 2026-10-30. Taak: securityreview van de gestagede diff voor issue #9.

## Wat ging goed

De opdracht noemde de vier toetspunten en de grenzen (geen testsuite, geen afbraak). Daardoor kon ik gericht werken. De draaiende stack stond al op migratie 0003, zodat ik de rechten en de index direct in de database kon nalezen.

## Wat kon beter

De opdracht noemde de databasegebruiker voor `psql` niet. Mijn eerste poging met `postgres` mislukte; de eigenaarsrol `botenloods` stond in `docker-compose.yml`.

## Wat deed ik zelf goed

Ik heb de rechten van beide rollen live opgevraagd en de openbare pagina live aangeroepen, in plaats van alleen de diff te lezen. Zo bleek dat de taakrol voor seed geen nieuwe rechten nodig heeft.

## Wat heb ik onderweg zelf verbeterd

Een tijdelijk HTML-bestand belandde in `/tmp` in plaats van in de scratchpad. Ik heb het direct verwijderd; een volgende keer gebruik ik de scratchpad.

## Wat kan structureel beter

Zet in de opdracht: "Database-controles in de db-container met `psql -U botenloods -d botenloods`."
