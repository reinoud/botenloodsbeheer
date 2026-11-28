# Treffers count(), all_inner_texts(), all_text_contents() in tests/e2e (#459)

Datum 2026-11-28. Regelnummers van vóór de wijziging, tenzij anders vermeld.

| Bestand:regel | Oordeel | Reden |
|---|---|---|
| test_import.py:120 | in orde | `expect(rijen.first).to_be_visible()` staat ervoor; `rekoverzicht.html` heeft geen `bl-lijst`, dus dat wacht op de nieuwe pagina |
| test_bootsoorten.py:61 | in orde | direct na `page.goto("/indeling")`; conditioneel opruimen |
| test_bootsoorten.py:67 | hersteld | tweede ronde leest direct na een verwijderklik (formulierpost); nu wacht `expect` op de melding "De bootsoort is verwijderd." |
| test_boot_verplaatsen.py:48 | in orde | geen navigatie in de lus (viewport en uitklapblok); `expect(keuze)` staat ervoor |
| conftest.py:56 (`blok_openen`) | hersteld | aanroepers als `test_beheerders.py:29` en `test_overloop.py:29` roepen hem direct na een navigerende klik aan; nu wacht een `expect` eerst op het blok met die titel |
| test_boten_zonder_plaats.py:24 | in orde | na `page.goto`, daarna alleen het openen van een uitklapkop |
| test_boten_zonder_foto.py:23 | in orde | idem |
| test_lid_koppeling.py:48, :53 | in orde | `rond()` wordt aangeroepen na `page.goto("/gebruikers")` en na `expect(treffer(...)).to_have_count(1)` |
| test_lid_koppeling.py:104 | hersteld | direct na `lid_zoeken` (klik op Zoeken, navigeert); de vorige zoekactie gaf nul treffers, dus `expect(...nth(1)).to_be_attached()` wacht op de nieuwe lijst |
| test_kaartjes.py:101 | hersteld | na `kiezen()` (GET-formulier, `wait_for_load_state` wacht niet op inhoud); vóór de klik staat het formulier `/kaartjes` zonder kaartjes, dus `count()` kon 0 tellen. Nu wacht `kiezen()` met `expect_navigation()` op de printpagina (review Sentinel) |
| test_inloggen.py:41, :43 | hersteld | in de lus volgde `count()` op `oudere.click()` plus `wait_for_load_state()`; nu `with page.expect_navigation()` om de klik. De eerste telling (regel 41) staat na `expect` op de nieuwe pagina |
| test_loods.py:129 | in orde | na `expect(lijst.or_(melding)).to_be_visible()` |
| test_overzichten.py:82 | in orde | na `page.goto` en `expect(rijen.first)` |
| test_overzichten.py:115 | in orde | na `page.goto` en `blok_openen` |
| test_status.py:89 | in orde | na `expect(heading "Boten in de loods")`, een kop die `/leden` niet heeft |
| test_status.py:94 | in orde | na `page.goto("/leden")` |
| test_uploadgrens.py:56 | in orde | na `page.goto("/instellingen")` |
| test_soort_kiezen.py:15 (`opties`), aanroep :34 en :37 | in orde | na `expect(een).to_be_visible()` op dezelfde pagina |
| test_soort_kiezen.py:63 (aanroep van `opties`) | hersteld | direct na de klik op "Keuzes opslaan"; nu `expect(...).to_be_visible()` op de keuzelijst van regel 4 (die stond er daarvoor nog niet) |
| test_wachtlijst.py:36 | in orde | na `page.goto("/wachtlijst")` en `expect` op de rij |
