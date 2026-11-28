# Terugblik Sentinel, review #459 (count() na een navigerende klik)

Datum: 2026-11-28. Taak: review vóór commit van de gestagede diff op `fix/459-e2e-count`.

## Wat ging goed

De opdracht noemde de twee lastigste punten (de opruimlus in `test_bootsoorten.py` en de wachtregel in `blok_openen`) en zei dat er geen mutant is. Daardoor lag de nadruk meteen op de vraag welke pagina er stond vóór de klik. De lijst `werk/459-treffers.md` maakte de steekproef snel: per treffer stond er een reden die ik tegen de code kon leggen.

## Wat kon beter

De oordelen in de trefferslijst gaan uit van de pagina vóór de klik, maar die staat soms in een helper. Bij `test_kaartjes.py` doet `kiezen()` eerst `page.goto("/kaartjes")`, dus de oude pagina is het keuzeformulier en niet de pagina per rek. De nieuwe regel `expect(page).not_to_have_url(per_rek)` slaagt daardoor direct op het formulier en wacht nergens op. De bouwer las de testregel, niet de helper.

## Wat deed ik zelf goed

Ik heb per aanroeper van `blok_openen` nagegaan wat de vorige pagina was en of daar een blok met dezelfde titel staat (`profiel.html` en `boot.html` tegen het rekoverzicht en `/boten`). Ook de indirecte aanroepers via `wachtwoord_instellen` en `logo_uploaden` heb ik meegenomen: dat zijn achttien bestanden die de bouwer niet draaide.

## Wat heb ik onderweg verbeterd

Ik wilde de achttien bestanden eerst in één aanroep van `draai.sh` draaien. Met 35 tests en de limiet van 20 inlogverzoeken plus 30 per minuut heb ik ze in drie groepen met 40 seconden pauze gezet.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Bepaal bij elke wachtregel na een klik eerst welke pagina er vóór de klik stond, ook als een helper daarvoor `page.goto` doet, en noem die pagina in de trefferslijst; een `expect` die op die pagina al slaagt, telt niet als wachten."
