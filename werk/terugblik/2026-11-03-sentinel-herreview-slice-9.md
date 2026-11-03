# Terugblik sentinel: herreview herstel slice 9

**Datum:** 2026-11-03
**Taak:** herreview van het herstel van slice 9 (issue #48): tokentest, losse E2E-test en twee ADR's

## Wat ging goed

De brief noemde de vier bestanden, de mutanten, de commandovorm en de nachtelijke omweg. Daardoor kon ik zonder zoeken toetsen. Werkmap en gestagede versie waren gelijk (`git diff --quiet`). Unit 467 geslaagd, losse E2E 4 geslaagd, s1 en m9 gevangen.

## Wat kon beter

De vraag "dekt de unittest BLB-026 criterium 5 nog" werd beantwoord door een docstring ("met tijdstip en aantallen") en niet door een assert. De test controleert alleen de aantallen. Een mutant die het tijdstip van de opschoning leeg laat, overleeft de hele suite. De E2E-docstring verwijst naar die dekking die er niet is.

De melding uit de vorige review dat m9 ook het filter weghaalt, kon ik niet reproduceren: m9 verschilt nu op één regel van de gestagede `status.py`.

## Wat deed ik zelf goed

Ik heb s1 gesplitst in twee mutanten, één per pad (robottokens en verlopende tokens). Beide worden apart gevangen. Zo is elke uitsluiting afzonderlijk getest, niet alleen samen.

## Wat heb ik onderweg verbeterd

Ik heb de bewering over de dekking zelf met een mutant getoetst (h3) in plaats van de docstring te geloven.

## Wat kan structureel beter

Zet in de opdracht: "Verplaats je de dekking van een criterium van E2E naar unittests, noem dan per gegeven uit het criterium (zoals tijdstip en aantallen) de assert die het dekt, en draai een mutant die dat gegeven weghaalt."
