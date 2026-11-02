# Terugblik forge, slice 8: kaartjes met QR-code

**Datum:** 2026-11-02
**Taak:** slice 8 bouwen (issue #46): keuzepagina, printpagina met acht kaartjes per A4, tests, handleiding en screenshot.

## Wat ging goed

De opdracht noemde wat al bestond (segno, `/p/<sleutel>`, logo) en wat nog niet, dus ik hoefde niet te zoeken. De bestaande functie `indeling.rekken()` gaf de volgorde van de loods en het voorladen van boot en lid; de kaartjes zijn daar een filter op. De zes mutanten op domein, route en template faalden allemaal tegen `tests/unit/test_kaartjes.py`.

## Wat kon beter

Mijn eerste E2E-test telde de kaartjes voordat de grote pagina van alle plaatsen geladen was, en zette de media terug op `screen`, waardoor `page.pdf()` de schermstijl gebruikte. Beide gaven een pagina te veel en kostten drie runs. Ook een proef met een clubboot op een gewone plaats was overbodig: de domeinregel verbiedt dat al.

## Wat deed ik zelf goed

Ik heb het extra pdf-blad eerst nagebootst met een losse Chromium-proef in de scratchpad, met en zonder echt logo, voordat ik de CSS aanpaste. Zo bleek dat de CSS klopte en de test fout zat.

## Wat heb ik onderweg verbeterd

De breedte van een blad staat nu vast (`width: max-content`), zodat de A4-controle in de test de echte inhoud meet. De vlag `club` is teruggebracht tot `is_clubplaats`, omdat een clubboot altijd op een clubplaats ligt.

## Wat kan structureel beter

- Zet in de opdracht: in een E2E-test met `page.pdf()` zet je de media terug met `emulate_media(media="no-override")`, niet met `"screen"`, en wacht je na een klik met `page.wait_for_load_state()` voordat je elementen telt.
- Zet in de opdracht: een nieuw menu-item verandert alle schermafbeeldingen met de kopbalk; die blijven dan staan en worden niet teruggezet.
