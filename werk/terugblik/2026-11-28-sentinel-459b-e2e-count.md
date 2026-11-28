# Terugblik Sentinel, tweede review #459 (herstel in `kiezen()`)

Datum: 2026-11-28. Taak: tweede review vóór commit van de gestagede diff op `fix/459-e2e-count`, met de nadruk op het herstel in `tests/e2e/test_kaartjes.py`.

## Wat ging goed

De opdracht noemde het afgekeurde punt, het herstel en de twee patchbestanden. Een `diff` van die twee liet in één keer zien wat er nieuw was: de klik in `kiezen()` staat in `expect_navigation()`, en `test_lid_koppeling.py` heeft een regel in twee delen. Alle vijf aanroepen van `kiezen()` staan in hetzelfde bestand, dus het nalopen kostte weinig.

## Wat kon beter

De opdracht vroeg of elke aanroep van `kiezen()` navigeert. Het antwoord stond niet in de test, wel in de route: `/kaartjes/print` geeft de printpagina of een redirect naar `/kaartjes` met een melding. Beide laden een nieuw document. Een verwijzing naar `app/web/overzichten.py` in de opdracht had dat zoeken bespaard.

De overlay (E2E, regel over `page.pdf()`) zegt nog dat je na een klik met `page.wait_for_load_state()` wacht voordat je telt. Direct na `click()` kan die aanroep op de oude pagina slagen. Dat was hier de oorzaak van het oude risico.

## Wat deed ik zelf goed

Ik heb per aanroep de pagina vóór de klik bepaald: steeds het formulier `/kaartjes` na `page.goto`, zonder `section.kaartje`. Ik heb gecontroleerd dat het formulier een GET zonder `required` en zonder script is, zodat ook `kiezen(page)` zonder keuze navigeert. Ik heb de testregel na het inkorten van het commentaar zelf los gedraaid met `-k`: 1 geslaagd, 0 mislukt, 0 overgeslagen.

## Wat heb ik onderweg verbeterd

`cmp` tussen de staging en `diff-459b.patch` gaf een verschil. Dat bleek alleen de drie werkbestanden te zijn die niet in de patch stonden; de testbestanden waren gelijk.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de overlay (E2E, regel over `page.pdf()`): "Wacht na een navigerende klik met `with page.expect_navigation():` om de klik of met een `expect` op een element dat alleen de nieuwe pagina heeft; `page.wait_for_load_state()` direct na `click()` kan op de oude pagina slagen (#459)."

Zet in de opdracht: "Noem bij een helper die een formulier verstuurt de serverroute, zodat de reviewer ziet welke antwoorden (pagina of redirect) elke aanroep kan geven."
