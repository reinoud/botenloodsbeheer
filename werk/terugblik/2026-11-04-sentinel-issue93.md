# Terugblik Sentinel, 2026-11-04

Taak: review vóór commit van app/api/openapi.yaml tegen issue #93.

## Wat ging goed
De diff was klein en het issue had heldere acceptatiecriteria. De regie gaf de uitkomst van de suite mee, zodat een tweede run niet nodig was.

## Wat kon beter
Lokaal ontbreekt PyYAML, dus een losse YAML-controle buiten de container lukte niet. De geldigheid van de spec steunt nu op de spectests in de suite.

## Wat deed je zelf goed
Per pad de methoden en requestBody nagelopen: alleen PUT /leden en POST /leden/import-mislukt nemen een lichaam aan, de rest is GET.

## Wat heb je onderweg verbeterd
Niets; de review vroeg geen herstel.

## Wat kan structureel beter in de opdracht of afspraken
Zet in de opdracht: "Een losse controle van de spec draait in de testcontainer (docker compose ... run --rm test python -c ...), niet met de python3 van de host."
