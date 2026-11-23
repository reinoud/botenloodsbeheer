# Terugblik Sentinel, herreview #381

**Datum:** 2026-11-23
**Taak:** herreview vóór commit van het herstel op de vier punten van de eerste review (issue #381)

Oordeel: akkoord. Unittests (`test_ongeldige_leden.py`, `test_leden.py`, `test_status_en_bootaantallen.py`) op een eigen testdatabase `botenloods_test_s381b`: 80 geslaagd, 0 gefaald, 0 overgeslagen. Mutant zonder de `update` in `_run_afsluiten` tegen `test_ongeldige_leden.py`: 2 gefaald, 19 geslaagd, 0 overgeslagen. Eigen mutant met de datums vóór de tekstvelden in `valideer` (`app/domein/leden.py:169`): 21 geslaagd, 0 gefaald, 0 overgeslagen. Die overleeft. ADR-004 stap 2 noemt de volgorde "tekstvelden, datums, naam", maar alleen datum vóór naam is getoetst. Advies, niet blokkerend: één geval `record("1", naam=7, lid_sinds="12-03-2019")` met reden "ongeldige tekst" in de parametrisering van `test_elke_reden_staat_bij_het_lidnummer`. Klein punt in ADR-010 (al akkoord in de eerste review): `null` staat er ook zonder import en na een mislukte import, de ADR noemt alleen "niets ongeldigs". De werkmap bleef ongewijzigd (`git diff --stat` leeg). De database `botenloods_test_s381b` blijft staan.

## Wat ging goed

De opdracht noemde de vier punten, de herstelde plekken en de mutanten die de regie al draaide. Daardoor kon ik gericht één mutant herhalen en één eigen mutant kiezen op het punt dat het minst gedekt leek.

## Wat kon beter

De opdracht zei dat Aegis tegelijk unittests draait op de gedeelde database, maar niet dat ik een eigen testdatabase moest gebruiken. Dat staat in de overlay; ik heb het daar gevonden.

## Wat deed ik zelf goed

Ik heb de mutant op de volgorde van de redenen zelf gekozen, omdat de nieuwe test maar één van de twee volgordes in de ADR dekt. Zo werd een gat zichtbaar dat de mutanten van de regie niet raakten.

## Wat heb ik onderweg zelf verbeterd

Mijn eerste mutantrun gebruikte `-rs`. Dat verbergt de namen van gefaalde tests in de samenvatting. Het aantal klopte met dat van de regie; bij een volgende run gebruik ik `-rfs`.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Draait een ander agent tegelijk unittests, gebruik dan een eigen testdatabase via een bind mount van een `conftest.py` met een andere `TEST_DB` (overlay, regel over twee agents), en draai pytest met `-rfs`."
