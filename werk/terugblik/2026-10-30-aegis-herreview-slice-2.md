# Terugblik aegis, securityherreview slice 2

**Datum:** 2026-10-30
**Taak:** herreview van de gestagede diff van slice 2 (issue #11) na herstel van de twee punten uit de eerste aegis-review, tegen ADR-001 v1.1.2.

## Wat ging goed

De brief noemde beide herstelpunten met bestand en de tests die ze dekken. Daardoor kon ik gericht toetsen: de volgorde van de decorators, `populate_existing` in `_eigen_account` en de nieuwe tests. Het herstel is klein en raakt geen andere aanroepers.

## Wat kon beter

De brief vroeg om te zoeken naar andere routes met blijvend effect, maar de ADR noemt alleen routes die een link opleveren. Of deblokkeren daaronder valt (het geeft een oud account zijn methodes terug), moest ik zelf afwegen.

## Wat deed ik zelf goed

Ik heb de suites niet opnieuw gedraaid en niets in de werkmap gewijzigd. Ik heb gecontroleerd dat `inloggen_vereist` vóór `recent_ingelogd` draait, zodat een bezoeker zonder sessie niet op de verkeerde plek uitkomt.

## Wat heb ik onderweg verbeterd

Ik heb het gedrag van `populate_existing` bij een al geladen relatie (`passkeys`) nagelopen in plaats van alleen de kolommen te controleren, omdat `methode_intrekken` de passkeys telt.

## Wat kan structureel beter

Zet in de opdracht: "Noem in de ADR per beheerroute (uitnodigen, herstellen, blokkeren, deblokkeren, verwijderen, methodes) of een recente inlog vereist is, zodat de reviewer tegen een lijst toetst en niet zelf hoeft af te bakenen."
