# Terugblik sentinel, 2026-11-27

Taak: review vóór commit van #458, `tests/e2e/test_status.py` (wachten op de lijst `#ongeldige-leden`).

## Wat ging goed

De brief noemde de logs met pad en tijdvak en zei wat de regie al had gedraaid. Daardoor kon ik de oorzaak toetsen zonder zelf de E2E te draaien.

## Wat kon beter

De brief noemde het verschil van 272 bytes als bewijs, maar niet of iemand had nagerekend dat de lijst precies die 272 bytes is. Dat heb ik zelf gedaan. De grep van de regie zocht alleen op `all_inner_texts` en `all_text_contents`; dezelfde fout kan ook met `count()` na een klik.

## Wat deed ik zelf goed

Ik heb de opmaak van de lijst uit `app/web/templates/status.html` met de vier verwachte regels nagebouwd: precies 272 bytes, gelijk aan het verschil in het log. De volgorde in `log-web.log` koppelt het verzoek van 16391 bytes aan de mislukte test en dat van 16119 bytes aan de eerste test van het bestand.

## Wat heb ik onderweg verbeterd

Ik heb de grep verbreed naar `count()`, `inner_text()` en `content()`. Daarbij vond ik twee plekken met dezelfde race: `tests/e2e/test_lid_koppeling.py:104` en `tests/e2e/test_kaartjes.py:101`.

## Wat kan structureel beter in de opdracht

Zet in de opdracht: "Grep bij een race na een klik op elke lezing die niet wacht (`all_inner_texts`, `all_text_contents`, `count()`, `is_visible()`, `content()`, `wait_for_load_state()` direct na `click()`), niet alleen op de functie uit de fout."
