# Terugblik bedrock, slice 12 (issue #80), backend
Datum: 2026-11-04. Taak: domein, tests, seed, rechten en migratie van de indeling met rek, verdieping en vak.

## Wat ging goed
- Het domein, de migratie en de seed stonden er al bijna; controleren en afmaken was snel.
- Het contract met de helper `plaats(...)` maakte de omzetting van de bestaande tests mechanisch.
- Mutanten per grens en per recht vingen precies de bedoelde tests.

## Wat kon beter
- Twee testruns tegelijk op `botenloods_test` blokkeerden elkaar (TRUNCATE tegen een open transactie). Ik verloor een kwartier voordat ik dat zag.
- Mutant m2 (geen slot op het rek) overleefde eerst: `race()` vangt alleen Regelfouten, een IntegrityError in de thread verdween stil.

## Wat deed ik zelf goed
- Een eigen testdatabase via een bind mount van een gewijzigde conftest, zodat mijn runs los stonden van andere agents.
- De racetest afgeleid van het gedrag zonder slot (de wachtende thread), niet van de uitkomst alleen.

## Wat heb ik onderweg verbeterd
- De racetest van het rek vangt nu onverwachte uitzonderingen in de thread op, waarna m2 faalt.
- `populate_existing` op de plaatsenquery blijkt overbodig (m3 overleeft, zie hieronder); ik heb het laten staan volgens de overlay.

## Wat kan structureel beter
- De testdatabase is niet per agent instelbaar. Een omgevingsvariabele `TEST_DB` in `tests/unit/conftest.py` voorkomt de botsing.
- `race()` zou onverwachte uitzonderingen van de actie moeten doorgeven.

## Als regel voor de volgende opdracht
- Zet in de opdracht: "Draai je tests op een eigen testdatabase (bind mount van een conftest met andere TEST_DB) zolang een andere agent op dezelfde stack test."
- Zet in de opdracht: "Een racetest met `race()` controleert ook dat de actie geen andere uitzondering dan Regelfout gooit."
