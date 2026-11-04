# Terugblik Sentinel, issue #92

Datum: 2026-11-04. Taak: review van de gestagede diff in `tests/e2e/draai.sh` (container weer starten na mislukte importaanvraag).

## Wat ging goed
De opdracht was klein en compleet: diff, criterium, testaanpak en de waarschuwing over `secrets/api_token`.

## Wat kon beter
Niets wezenlijks. De stub moest ook de `config`-aanroepen van regel 17 tot 24 afvangen; dat stond niet in de opdracht.

## Wat deed je zelf goed
Het token vooraf gekopieerd en teruggezet, en met `git status` gecontroleerd dat de werkmap ongewijzigd bleef.

## Wat heb je onderweg zelf verbeterd
De stub laat `config -q` falen en geeft bij `config` de whitelistregel terug, zodat het script tot de importaanvraag komt.

## Wat kan structureel beter in de opdracht of de afspraken
Zet in de opdracht: een docker-stub voor draai.sh moet `config -q` laten falen en bij `config` de regel `sourcerange: 192.0.2.0/24` geven, anders stopt het script vóór de te testen regel.
