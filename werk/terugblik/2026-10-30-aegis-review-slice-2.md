# Terugblik aegis, securityreview slice 2

**Datum:** 2026-10-30
**Taak:** securityreview van de gestagede diff van slice 2 (BLB-023, BLB-038, BLB-004), tegen ADR-001 v1.1.1 en overlay §5.

## Wat ging goed

De brief noemde de norm met de drempels (10 minuten, 5 pogingen, 15 minuten, 12 uur) en het ADR-pad. Daardoor kon ik direct toetsen in plaats van de norm te zoeken. De code is klein en leesbaar; de domeinfuncties vergrendelen rijen en de logregels bevatten geen code of geheim.

## Wat kon beter

De brief vroeg om de recente inlog bij methodes toevoegen en intrekken. Dat uitnodigen en herstellen nu ook via de webinterface lopen, en daarmee dezelfde aanhoudende toegang geven, stond niet in de brief en ook niet in de ADR. Dat vond ik pas door te vergelijken met HEAD (uitnodigen was alleen CLI).

## Wat deed ik zelf goed

Ik heb een vermoeden over verouderde attributen na `get(..., with_for_update=True)` niet als feit gemeld, maar eerst in de web-container nagebootst met een losse SQLAlchemy-proef in mijn scratchpad. De proef bevestigde het. De testsuite heb ik niet gedraaid, zoals gevraagd.

## Wat heb ik onderweg verbeterd

Mijn eerste proef draaide met een relatief databasepad dat in de container niet schrijfbaar was; ik heb het pad naar een tijdelijk bestand in de container gezet en dat na afloop verwijderd. Tekstwijziging in de proef met python3 in plaats van sed, volgens de checklist.

## Wat kan structureel beter

Zet in de opdracht: "Komt een handeling die eerst alleen via de CLI kon nu in de webinterface (zoals uitnodigen), noem dat in de brief aan de reviewer en zeg of de regel voor een recente inlog daar ook geldt."

Zet in de opdracht: "Een race-test voor een domeinfunctie laadt het object eerst in dezelfde sessie, zoals `before_request` dat doet, zodat verouderde attributen na `with_for_update` zichtbaar worden."
