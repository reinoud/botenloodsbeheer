# Terugblik Sentinel, review #395 (Leden: filter zonder knop)

Datum: 2026-11-24. Taak: review van de gestagede diff op `feature/leden-lijstfilter` tegen issue #395.

## Wat ging goed

De brief noemde de drie toetspunten, de commando's en de telling van de regie. De mutanten waren daardoor in één ronde te draaien: vier kopieën van `app` in de scratchpad, één run per mutant.

## Wat kon beter

De bouw zette de lijst in een `div data-lijstdeel`, maar zocht niet naar `main > ul.bl-lijst` in andere E2E-tests op `/leden`. `tests/e2e/test_status.py:83` valt daardoor. De regie draaide alleen `test_lijstfilter.py` en `test_overzichten.py`, dus de val bleef buiten beeld. De regel uit de overlay (#380, wrapper om een blok) bestond al, maar werd niet toegepast.

## Wat deed ik zelf goed

Ik zocht eerst met `grep` naar selectors met `main >` en draaide de verdachte test los, voordat ik de opgegeven set draaide. Zo kwam de regressie met bewijs uit één run van 34 seconden.

## Wat heb ik onderweg verbeterd

Bij het importblok keek ik verder dan de vraag "staat het buiten het lijstdeel". Een mutant die het blok in het lijstdeel zet, overleeft de unittest. De E2E-assert "Import zichtbaar" vangt hem ook niet, omdat het script dan een verse kopie van het blok terugzet.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Zet je een blok in een omhullende `div`, draai dan elk E2E-bestand dat `main >` gebruikt op dat scherm (`grep -rln 'main >' tests/e2e/`), niet alleen de bestanden van de feature, en noem ze in de reviewbrief."
