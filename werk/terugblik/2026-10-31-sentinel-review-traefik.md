# Terugblik Sentinel: review Traefik (#29) en beheerdocumentatie (#30)

**Datum:** 2026-10-31
**Taak:** review vóór commit van de gestagede wijziging; als enige de suites draaien op de gedeelde stack.

## Wat ging goed

De opdracht noemde de drempels, de ADR, de proeven en de taakverdeling met Aegis. Daardoor kon ik direct toetsen. De stack was al gebouwd met de gestagede `Dockerfile` (de `CMD` met de loggerklasse stond in de container), dus een `up --build` was niet nodig. Unit 330 geslaagd, E2E 25 geslaagd in 6 bestanden, één test los met `-k` geslaagd, niets overgeslagen.

## Wat kon beter

De scratchpad was gedeeld met eerdere agents (bestanden als `api.py` en `e2e-1.txt`). Een naam als `e2e.log` kan zo botsen. Mijn eerste mutantrun gaf geen uitvoer omdat `tail` op de pijp niets doorgaf; de tweede run schreef naar bestanden.

## Wat deed je zelf goed

Mutanten op drie plekken: de envtest (een variabele uit de documentatie, een nieuwe variabele in `.env.example`), de toegangslog (querystring, healthcheck) en de controle op de certresolver. Alle vijf faalden. De logcontrole deed ik met een uniek kenmerk in pad en querystring, zodat de E2E-suite die tegelijk liep de telling niet verstoorde.

## Wat heb je onderweg zelf verbeterd

Mutantuitvoer naar een bestand in de scratchpad in plaats van naar een pijp, en `cmp` vooraf, zodat een mutant die gelijk is aan het origineel opvalt.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Geef elk agent een eigen submap in de scratchpad (`<scratchpad>/<agent>-<taak>/`), want de scratchpad wordt gedeeld tussen agents van dezelfde sessie."

Zet in de overlay: "De regel 'herstart ook de proxy na `up --build`' vervalt onder ADR-013; Traefik volgt de containers zelf."
