# Terugblik: herreview #32 en #40

Datum: 2026-11-03
Taak: tweede review van de gestagede diff van `tests/e2e/draai.sh` en `tests/unit/test_beheerders_beheren.py`.

## Wat ging goed

De opdracht noemde elke context waarin het script `robot` of `token` aanroept. Daardoor was de proef in één ronde compleet. Het verbod op draai.sh, de unitsuite en containers op de gedeelde stack was duidelijk.

## Wat kon beter

De twee nieuwe regels onder E2E in de overlay (v0.4.6) gaan over tabelselectors, pdf-tests en het verplaatsen van dekking. Ze raken deze diff niet. De opdracht had kunnen zeggen welke regel voor deze review telt.

## Wat deed ik zelf goed

Ik draaide de echte draai.sh uit de index (`git show :tests/e2e/draai.sh`) tegen een stub voor `docker` en `sleep` in de scratchpad. Elk foutpad gaf exit 1, geen pytest-run en de stderr van de tokenaanmaak. De geslaagde run gaf alle acht namen van omgevingsvariabelen met de juiste waarde.

## Wat heb ik onderweg zelf verbeterd

Ik vergeleek de namen van de omgevingsvariabelen niet alleen in de tekst van het script, maar ook in de uitvoer van de stub. De namen voor api, tempo, prefix, ingetrokken en import ontstaan nu met `tr` in een lus en staan niet meer letterlijk in het script.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Proef een shellscript met de versie uit de index (`git show :pad`) in de scratchpad, met een stub voor externe commando's, en vergelijk de uitvoer van een geslaagde run met die van vóór de wijziging."
