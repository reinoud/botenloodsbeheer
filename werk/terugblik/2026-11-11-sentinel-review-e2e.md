# Terugblik Sentinel: review wisselvallige E2E (#172, #217, #213)

Datum: 2026-11-11. Taak: review vóór commit van de gestagede diff op `fix/172-217-213-e2e`.

## Wat ging goed
- De brief noemde per toetspunt hoe het bewijs eruit moest zien (mutant via `DRAAI_OVERRIDE`, ruis van een andere actie). Daardoor stond het ontwerp van beide proeven vooraf vast.
- De mutant op `inloggen.html` liet zich met één bind mount op `web` draaien, zonder de werkmap te raken. De test viel er direct op (1 alert in plaats van 0).

## Wat kon beter
- De brief zei niet of de unitsuite en de E2E-suite tegelijk mochten draaien. Ik draaide de unitsuite tijdens de mutantproef, omdat die een eigen testdatabase gebruikt, en de volledige E2E-run pas daarna.
- De terugblik van de bouwer meldde de ruis in het log, niet de ruim honderd beheerders `e2e-ruis-*` die zijn proef achterliet. `opruimen.sql` laat ze staan als twijfelgeval.

## Wat deed je zelf goed
- Ruis rechtstreeks via `log.schrijf` in `web` geschreven, met de actie `sentinel.ruis`, zodat er geen beheerders achterblijven. Een kleine test in de scratchpad wacht op een markering tot de ruis staat, en draait vóór `test_inloggen.py` in dezelfde pytest-aanroep.
- 120 ruisregels in plaats van 50: de uitnodiging kwam op pagina 3 te staan, dus de lus moest twee keer doorklikken.

## Wat heb je onderweg verbeterd
- De oude test niet via een kopie buiten `/e2e` gedraaid (dan ontbreekt `conftest.py`), maar als bind mount over `/e2e/test_inloggen.py`.

## Wat kan structureel beter
Zet in de opdracht: een volgordeproef op het log schrijft ruis met `log.schrijf` via `docker exec` in `web`, niet via de interface, zodat er geen beheerders of andere gegevens achterblijven die `opruimen.sql` laat staan.
