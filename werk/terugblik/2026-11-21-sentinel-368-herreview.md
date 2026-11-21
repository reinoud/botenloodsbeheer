# Terugblik Sentinel, herreview #368

Datum: 2026-11-21. Taak: herreview van de delta in `tests/e2e/draai.sh` (secrets-controle met realpath, melding zonder integratiecontainer).

## Wat ging goed
De delta was klein en de opdracht noemde de routes precies. Een stub voor `docker` met regels 7 en 61 tot 71 van het script was genoeg om alle routes te toetsen onder `set -euo pipefail`.

## Wat kon beter
Mijn eerste proefcommando begon met `rm -rf` op de scratchpad. Dat bleef tien minuten hangen op een akkoordvraag en is niet uitgevoerd.

## Wat deed je zelf goed
Ik heb naast de vijf routes ook een bron getoetst die niet bestaat, en een pad met een symlink (`/tmp` naar `/private/tmp`). Beide gedragen zich goed.

## Wat heb je onderweg verbeterd
Ik ben verdergegaan in een nieuwe map zonder iets te verwijderen.

## Wat kan structureel beter in de opdracht
Zet in de opdracht: proeven in de scratchpad gebruiken een nieuwe submap en verwijderen niets.
