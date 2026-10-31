# Terugblik Sentinel, review gebruikersdocumentatie (issue #30)

Datum: 2026-10-31. Taak: review vóór commit van de handleiding, de screenshots, het screenshotscript en `tests/unit/test_documentatie.py`.

## Wat ging goed
De opdracht noemde de drempels en de ADR, de grens van de commit en de mutantmethode met bind mount. Daardoor kon ik direct toetsen. De suite slaagde in één run.

## Wat kon beter
De 20 screenshots één voor één bekijken kost veel context. Een lijst met de schermen die geheimen of persoonsgegevens kunnen tonen, had de controle sneller gemaakt.

## Wat deed je zelf goed
De mutant verwijdert een route die maar één keer in de handleiding staat (`/huisstijl.css`). Zo faalt de test echt op die ene route en niet toevallig op een andere plek. Ik heb ook gekeken of de PNG-bestanden tekstblokken met metadata bevatten.

## Wat heb je onderweg zelf verbeterd
Eerst wilde ik `/vrij` als mutant nemen, maar die route staat al in de ingebouwde mutanttest en komt vaker voor. Ik koos een route die maar één keer voorkomt.

## Wat kan structureel beter
Zet in de opdracht: "Noem de screenshots die geheimen of persoonsgegevens kunnen tonen; de reviewer bekijkt die eerst en de rest steekproefsgewijs."
Zet in de opdracht: "Een script met een eigen compose-project noemt welke images het bouwt en of het die na afloop laat staan."
