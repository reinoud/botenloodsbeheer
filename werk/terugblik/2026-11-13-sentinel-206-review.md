# Terugblik sentinel, review #206 Boot verplaatsen

**Datum:** 2026-11-13
**Taak:** review vóór de commit van issue #206 (branch `feature/206-boot-verplaatsen`)
**Oordeel:** niet akkoord (twee mechanische herstelpunten: ruff in het nieuwe testbestand, en ADR-006 regel 39 en 41)

## Wat ging goed

De brief noemde per toetspunt de mutanten die ik zelf moest draaien en wat buiten de review viel. Daardoor kon ik zonder zoeken beginnen. De bouwer had de racetests volgens de overlay opgezet (eerste sessie doet dezelfde wijziging, exacte vergelijking van de meldingen). Beide lockmutanten vielen op `tests/unit/test_boot_verplaatsen.py:149`.

## Wat kon beter

De brief vroeg niet om een lintrun. De 14 ruff-meldingen in het nieuwe testbestand vond ik pas aan het eind, terwijl de rest van de repository schoon is. Het brieftoetspunt "ADR-006 consistent met de code" noemde de alinea Twee logs, maar niet de tabel Tonen. Daar staat de filter van Vrije plaatsen nog als `plaats.`.

## Wat deed ik zelf goed

Naast de gevraagde mutanten draaide ik een mutant per aanroep van de macro `plaatsopties` en een losse proef op escaping van de reknaam in beide keuzelijsten. Zo is toetspunt 3 bewezen met tests die vallen, en niet alleen met tests die slagen.

## Wat heb ik onderweg verbeterd

De mutant "zonder FOR UPDATE op de nieuwe plaats" kan op twee manieren: de hele `with_for_update` weghalen (raakt ook de oude plaats) of alleen de nieuwe plaats buiten de vergrendeling lezen. Ik heb beide gedraaid. Alleen de tweede bewijst dat de nieuwe plaats zelf vergrendeld moet zijn.

## Wat kan structureel beter

Zet in de opdracht: "Draai `ruff check --no-cache app tests` in de testcontainer vóór de oplevering; de repository heeft nul meldingen, en een melding in de diff blokkeert de review."

Zet in de opdracht: "Voegt een wijziging een logactie toe of verandert een logfilter, zoek dan in ADR-006 in de alinea Twee logs én in de tabel Tonen, en in de handleiding in de alinea over de logs per scherm."
