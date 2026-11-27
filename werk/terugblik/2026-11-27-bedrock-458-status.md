Datum: 2026-11-27. Taak: oorzaak van #458 (E2E-test ongeldige leden op /status faalt eenmalig).

## Wat ging goed

De logs van pipeline-456 waren genoeg. De webgrootte van `GET /status` (16391 bytes, de pagina na de
PUT) tegenover de eerdere statuspagina zonder lijst (16119) laat zien dat de server de lijst leverde.

## Wat kon beter

Ik kon de race niet zelf reproduceren: E2E draaien en een eigen stack starten waren uitgesloten. De
oorzaak is daarom aangetoond uit de logs en de Playwright-semantiek, niet met een falende test.

## Wat deed je zelf goed

Eerst de serverkant uitgesloten: `app/` kiest de laatste run correct en `tests/unit/test_ongeldige_leden.py`
dekt de pagina al. Een meting (scratch) gaf 257 bytes extra voor een lijst van vergelijkbare omvang.

## Wat heb je onderweg verbeterd

Een eigen imagetag gebouwd (`botenloods-458b`) zodat `botenloods-dev` niet is aangeraakt. Het
tijdelijke meetbestand in `tests/unit` is na gebruik verwijderd.

## Wat kan structureel beter in de opdracht

De opdracht eiste een unittest die faalt op de huidige code. Bij een fout in de E2E-test zelf kan dat
niet. Ook sleept de verdenking naar tijdzone en sortering mee, terwijl de statusroute eerst met de
weblog (verzoekvolgorde en paginagrootte) te toetsen was.

## Als regel die de regie letterlijk kan overnemen

Zet in de opdracht: bij een E2E-fout waarbij de server het goede antwoord leverde (weblog: paginagrootte
en volgorde), is de oorzaak de test; zoek dan eerst `all_inner_texts`, `inner_text` of `count()` na een
klik zonder `expect`, want die wachten niet. Herstel met `expect(...).to_have_text(...)` of
`to_have_count`. Zonder E2E-run is een falende unittest dan niet mogelijk; accepteer logbewijs.
