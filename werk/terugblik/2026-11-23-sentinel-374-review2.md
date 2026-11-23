# Terugblik Sentinel, 2026-11-23

**Taak:** tweede review van `tests/e2e/draai.sh` voor #374 (herstel van het terugzetten van het tokenbestand in `opruimen`).

## Wat ging goed
De opdracht was smal en noemde de regel, het verwachte gedrag en de map voor de proef. De functie `opruimen` liet zich met `sed` uit het script knippen en met een stub voor `${c[@]}` draaien, zonder Docker.

## Wat kon beter
Mijn eerste proefcommando had een `rm -f` met variabelen en bleef tien minuten hangen op een goedkeuring. Ook `ls` brak af in deze omgeving; `[ -e ]` werkte wel.

## Wat deed je zelf goed
Ik heb drie gevallen gedraaid: terugzetten mislukt na een geslaagde run, terugzetten mislukt na een mislukte run, en terugzetten lukt. In alle drie liepen herstart, `opruimen.sql` en het verwijderen van de kopie door.

## Wat heb je onderweg zelf verbeterd
De proef opnieuw opgezet zonder `rm`: een apart logbestand per run en losse kop- en staartbestanden in de scratchpad.

## Wat kan structureel beter
Zet in de opdracht: "Proeven in de scratchpad gebruiken geen `rm` met variabelen; geef elke run een eigen bestandsnaam."
