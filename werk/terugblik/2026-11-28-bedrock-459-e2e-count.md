# Terugblik Bedrock, #459 E2E count() na navigatie

Datum 2026-11-28. Taak: `count()`, `all_inner_texts()` en `all_text_contents()` in `tests/e2e` die na een navigatie niet wachten.

## Wat ging goed

- De opdracht noemde de grep, de beoordelingsregel en de uitzondering voor opruimen. Daardoor was het oordeel per treffer snel te geven.
- Het overzicht staat in `werk/459-treffers.md`; de acceptatiecriteria zijn daarmee aantoonbaar nagelopen, niet alleen de twee regels uit het issue.
- De E2E-stack draaide al en `web` had `compose.dev.yml`; negen bestanden (19 tests) slaagden in één run.

## Wat kon beter

- Het issue noemde twee regels, maar de grep leverde meer risicovolle plekken op: een helper (`blok_openen`) en twee lussen (`test_inloggen`, `test_bootsoorten`). Het issue had dat kunnen zeggen: "ook helpers die `count()` bevatten".
- Een treffer in een helper is niet te beoordelen zonder alle aanroepers. Dat kostte de meeste tijd.
- De grep in de opdracht mist `opties(...)`-achtige wrappers: `all_text_contents()` zit in `test_soort_kiezen.opties()` en het risico zit in de aanroep op regel 63.

## Wat deed je zelf goed

- Zocht bij elke treffer de aanroepers op (`blok_openen`, `rond`, `opties`) voordat ik oordeelde.
- Controleerde dat `rekoverzicht.html` geen `bl-lijst` bevat, zodat het oordeel bij `test_import.py:120` onderbouwd is en niet uit het hoofd.
- Controleerde dat het formulier van `/kaartjes` een GET is, dus dat de URL van "Alle plaatsen" verschilt van die van het rek.

## Wat heb je onderweg zelf verbeterd

- Mijn eerste correctie voor `blok_openen` stond op één regel van 141 tekens; het commentaar staat nu op een eigen regel (max 100).
- Een `expect` op een locator met meerdere treffers geeft een strict-mode-fout; daarom `.first` in `blok_openen`.

## Wat kan structureel beter in de opdracht of de afspraken

- Zet in de opdracht: "Loop ook de helpers in `conftest.py` na en zoek hun aanroepers; een `count()` in een helper telt voor elke aanroeper."
- Zet in de opdracht: "Noem de mutant of de reden waarom een tijdwinst-race niet te muteren is; zonder dat is groen geen bewijs." Deze wijzigingen zijn niet gemuteerd: de race is niet af te dwingen.
- Zet in de overlay (E2E, regel #458) ook `locator(...).count()` binnen een wrapper als `opties()` en een `while`-lus met `count()` na `click()`.
