# Terugblik sentinel, review #380

**Datum:** 2026-11-23
**Taak:** review vóór de commit van issue #380 (filters zonder knop op /vrij, /wachtlijst en /boten)

## Wat ging goed

De brief noemde het filter voor `draai.sh -k`, de leidende besluiten in het issuecommentaar en dat aegis geen tests op de stack draait. Daardoor kon ik `web` zonder overleg vijf keer met een mutant opnieuw aanmaken. De E2E-runs duurden elk ruim 30 seconden, dus twee runs en vijf mutanten pasten ruim in de sessie.

## Wat kon beter

De overlayregel over een E2E-mutant op `app/web/static/` zegt dat een bind mount niet kan en dat het agent het bestand in de werkmap moet legen. De werkwijze voor een templatemutant (override op `web`, opnieuw aanmaken, controleren met `cmp`) werkt ook voor een statisch bestand. De twee regels spreken elkaar tegen.

## Wat deed ik zelf goed

Per besluit een eigen mutant (drempel, statusveld, knop, hele pagina, focus), elk met `cmp` in de container gecontroleerd vóór de run, en `web` daarna teruggezet en gecontroleerd. Ik voorspelde vooraf dat de mutant "hele pagina" op /vrij niet op de focus zou vallen (de `autofocus` van de keuzelijst) maar op het statusveld; dat klopte.

## Wat heb ik onderweg zelf verbeterd

Ik draaide het unittestbestand met een eigen `TEST_DB` via een kopie van `conftest.py`, zodat de suite van de regie niet verstoord raakt.

## Wat kan structureel beter

Zet in de overlay (E2E): "Een E2E-mutant op een bestand in `app/web/static/` draait als `:ro` bind mount via een override op `web`, op dezelfde manier als een templatemutant; de werkmap blijft ongewijzigd." Deze regel vervangt de regel die zegt dat het bestand in de werkmap geleegd moet worden.
