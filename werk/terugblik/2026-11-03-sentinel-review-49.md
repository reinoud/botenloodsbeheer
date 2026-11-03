# Terugblik sentinel, review issue #49

**Datum:** 2026-11-03
**Taak:** review vóór commit van de gestagede diff voor issue #49 (opschoning neemt het importslot)

## Wat ging goed

De brief noemde de gekozen oplossing, het testcommando, de verwachte mutantuitkomst en de plek in de integratiecontainer die geraakt kon worden. Daardoor kon ik direct gericht lezen. De mutant (HEAD-versie van `opschonen.py` als bind mount) faalde zoals gemeld: de opschoning verwijderde het lid (`leden: 1`). De volledige unitsuite gaf 468 geslaagd, 0 mislukt, 0 overgeslagen en 0 errors. Ruff gaf geen meldingen op de twee gewijzigde Python-bestanden.

## Wat kon beter

De brief vroeg naar het gevolg in de integratiecontainer, maar niet naar de documentatie voor wie de API aanroept. `documentatie/beheer/integratiecontainer.md` regel 76 en `app/api/openapi.yaml` regel 102 tot 104 noemen een 409 alleen bij een lopende import. Dat vond ik pas via een grep op "409".

## Wat deed ik zelf goed

Ik heb vóór de testrun met `git diff --stat` gecontroleerd dat er geen niet-gestagede wijzigingen waren, en de mutant met `cmp` tegen de werkmap vergeleken. Het commando staat in `commando.txt` naast de mutant in de scratchpad.

## Wat heb ik onderweg verbeterd

Ik heb de 409-afhandeling in `Koppeling.ronde` nagelopen voor beide gevallen: een verzoek van een beheerder blijft open en volgt de volgende ronde, een geplande import wacht een uur. Dat is aanvaardbaar, want de opschoning duurt seconden. Het commentaar op regel 112 noemt de opschoning nog niet als oorzaak; dat heb ik als opmerking meegegeven.

## Wat kan structureel beter in de opdracht

Zet in de opdracht: verandert een wijziging wanneer een API-route een foutcode geeft, noem dan ook de documentatie en de OpenAPI-beschrijving van die route, zodat de bouwer en de reviewer ze in dezelfde ronde bijwerken.
