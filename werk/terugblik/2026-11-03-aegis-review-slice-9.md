# Terugblik aegis, securityreview slice 9

Datum: 2026-11-03
Taak: securityreview van de gestagede diff van slice 9 (issue #48)

## Wat ging goed

De brief noemde de ADR's, de rechten die ik moest zien en de container op het netwerk `koppeling`. Daarmee kon ik de rechten in de database en de 403 via de proxy direct controleren, met een positieve controle (200 met het recht) ernaast.

## Wat kon beter

De brief zei dat de opschoning foto's op schijf verwijdert. Foto's staan in de database (ADR-008). Dat kostte een extra controle.

## Wat deed ik zelf goed

Ik heb twee eigen tokens gemaakt met een geldigheid van één dag, de waarden alleen in de scratchpad met mode 0600 bewaard, en beide na de proef ingetrokken en de bestanden verwijderd. `secrets/api_token` heb ik niet aangeraakt.

## Wat heb ik onderweg verbeterd

Mijn eerste curl ging naar poort 443; de lokale proxy luistert op 8080. Ik heb de poort eerst opgezocht in plaats van verder te gokken.

## Wat kan structureel beter

Zet in de opdracht: "Een domeinfunctie die rijen verwijdert op basis van een eerder gelezen lijst van id's, herhaalt de voorwaarde in de `DELETE` of neemt het slot van de taak die die voorwaarde kan wijzigen (zoals de import)."

Zet in de opdracht: "Noem de poort van de lokale proxy (`127.0.0.1:8080`, Host `localhost`) in elke brief aan een reviewer die via de proxy controleert."
