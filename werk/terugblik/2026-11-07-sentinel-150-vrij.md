# Terugblik Sentinel, review scherm Vrije plaatsen

**Datum:** 2026-11-07
**Taak:** review vóór de commit van het scherm Vrije plaatsen (`/vrij`), issue #150 deel 2, BV-44

## Wat ging goed

De brief noemde de bronnen, de bekende testuitkomst, de bekende E2E-fout (#172) en de mutanten die de bouwer al had gedraaid. Daardoor kon ik direct toetsen. Alle vier templatemutanten draaiden als bind mount en vielen elk op een assert met een eigen melding.

## Wat kon beter

De mutant zonder enkelvoud en de mutant zonder `|lower` vallen op dezelfde assert (`tests/unit/test_overzichten_en_instellingen.py:73`). Dat is genoeg om beide te vangen, maar één assert bewijst daar twee criteria. Ik wachtte op het einde van de volledige E2E-run met `pgrep -f draai.sh`; dat raakt ook de wachtlussen van mij en andere agents, die zelf `draai.sh` in hun commando hebben, en eindigt dus nooit. `kill -0` op de pid van het script werkte wel. Een E2E-mutant op het zelf versturen kon ik niet draaien: `vrij.js` staat in `app/web/static/` en de brief gaf geen toestemming om de werkmap tijdelijk te wijzigen. Het oordeel over de zwakke E2E-assert rust daarom op de unittest en op redeneren.

## Wat deed ik zelf goed

Elke mutant gemaakt met een telling dat de vervangen tekst precies één keer voorkomt, met een diff tegen `git show :pad` gecontroleerd, en het commando vastgelegd in `commando.txt` in de scratchpad. Naast de drie gevraagde mutanten ook een mutant zonder de knop gedraaid.

## Wat heb ik onderweg verbeterd

Voor de mutant met het script gecontroleerd dat `{% endblock %}` twee keer voorkomt en het blok `scripts` daarom achter het laatste geplakt, in plaats van een vervanging die beide raakt.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: wil je dat een E2E-mutant op een bestand in `app/web/static/` draait, geef dan toestemming om dat bestand tijdelijk in de werkmap terug te zetten en met `cmp` te herstellen; zonder die toestemming toetst de reviewer dat gedrag alleen met de unittest.

Zet in de opdracht: wacht op het einde van `draai.sh` met `kill -0 <pid>` of met `docker ps`, nooit met `pgrep -f draai.sh`; dat telt ook de wachtlussen van andere agents mee.
