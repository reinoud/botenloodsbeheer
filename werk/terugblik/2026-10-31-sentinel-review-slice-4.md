# Terugblik: review slice 4 (issue #18)

Datum: 2026-10-31. Taak: review van de gestagede wijziging van slice 4 (logo uit de installatie, "(geschikt voor …)" in de export), suites draaien, migratie 0004 controleren.

## Oordeel

**Akkoord.** Geen bevinding van ernst middel of hoger. Drie punten van ernst laag, waarvan één een keuze voor de stakeholder is.

## Testaantallen

- Unit (`run --rm test`): 219 geslaagd, 0 mislukt, 0 errors, 0 overgeslagen.
- E2E (`tests/e2e/draai.sh`): 13 geslaagd in 4 bestanden (3, 4, 3, 3), 0 mislukt, 0 overgeslagen.
- E2E los: `-k test_huisstijl_instellen_en_terugzetten`: 1 geslaagd, 12 niet geselecteerd.
- Mutant (grens van 10 MB weg in `app/web/huisstijl.py`, via een volume uit de scratchpad): `pytest -k ongeldig_logo` geeft 1 mislukt, 4 geslaagd. De mutant valt dus op.
- Live: `POST`/`GET /instellingen/logo` op `web` geeft 404. De containerlog meldt "Logo geladen uit /app/tests/fixtures/logo.png."

## Dekking per criterium

| Criterium | Test | Stand |
|---|---|---|
| BLB-027 c2: geldig logo op alle pagina's, ook openbaar, zonder metadata, geen logregel | `test_logo_uit_installatie_op_alle_paginas_zonder_metadata` (EXIF met GPS, 800 px, `/inloggen` en `/p/<sleutel>`, cache-headers, 404 bij verkeerd kenmerk, geen logregel `instelling.*`, niets in `afbeelding`); E2E `test_huisstijl_instellen_en_terugzetten` (bezoeker ziet `img.logo` met `/logo/<16 hex>`) | gedekt |
| BLB-027 c2: nieuw logo na herstart | `test_nieuw_logo_na_herstart_krijgt_nieuwe_url` (laadt twee keer, ander kenmerk) | gedekt, als nabootsing van de herstart |
| BLB-027 c3: ontbrekend of ongeldig, alleen de naam en melding in de log | `test_ontbrekend_of_ongeldig_logo_toont_alleen_de_naam` (ontbreekt, tekst, SVG, GIF, groter dan 10 MB; WARNING in de log) | gedekt |
| BLB-027 c4: geen upload of verwijderknop, route weg | `test_geen_logo_uploaden_of_verwijderen` (404 op de oude route); E2E (geen `input[type=file]`) | gedekt |
| BLB-027 c5: migratie verwijdert een geüpload logo | `test_migratie_verwijdert_geupload_logo` (logo weg, foto blijft, rij `logo` weg, CHECK weigert `logo`, downgrade staat `logo` weer toe); `test_migratie_omkeerbaar_en_gelijk_aan_modellen` | gedekt |
| BLB-017 c3 met vraag 11 en 19: "(geschikt voor …)" bij vrije plaats en clubplaats zonder boot | `test_export_kolommen_en_geen_contactgegevens` (A01, A04 vrij; A05 clubplaats zonder boot); E2E `test_vrije_plaatsen_indeling_op_telefoon_en_export` | gedekt |
| Worker leest geen logo (ADR-008) | `test_worker_leest_geen_logo` | gedekt |

## Migratie 0004

- Eén head: `alembic heads` geeft `0004 (head)`.
- Downgrade naar 0003 zet de regel terug op `soort IN ('foto','logo')`. Upgrade naar head zet hem op `soort = 'foto'`. `alembic current` daarna: `0004 (head)`.
- Rechten van `botenloods_web` en `botenloods_taken` op `afbeelding` en `instelling` vóór en na de ronde gelijk (SELECT, INSERT, UPDATE, DELETE; diff leeg).
- De upgrade verwijdert eerst de rijen en zet daarna de strengere regel, in één transactie (PostgreSQL). De volgorde klopt.
- De downgrade is aanvaardbaar. Het verwijderen van het logo is het doel van de stakeholder (besluit 2026-10-31, BLB-027 c5) en de docstring van de migratie zegt dat de downgrade het logo niet terugzet. Na een downgrade is er geen logo in de applicatie en ook geen uploadroute meer in deze code, dus er ontstaat geen halve toestand.

## Bevindingen

1. **Bootsoortnamen in kleine letters** (`app/domein/indeling.py:82`). Ernst: laag. Soort: onlogisch gedrag, naar de stakeholder (via regie of apex).
   `geschikt_voor` zet elke naam in kleine letters. De export toont daardoor "(geschikt voor c11)" en "(geschikt voor kajak, canadese kano)", terwijl een bezette plaats in dezelfde kolom "Kajak" en "C11" toont. Het criterium schrijft "(geschikt voor kajak, surfski)" in kleine letters, dus de code volgt de letter van het criterium. Voor "C11" en "Canadese kano" (intake regel 22) leest de kleine letter als een fout. Keuze voor de stakeholder: namen zoals beheerd (`s.naam`, dan wordt het criterium "(geschikt voor Kajak, Surfski)") of kleine letters houden. Bij namen zoals beheerd verdwijnt `.lower()` en wijzigen de verwachtingen in de unit- en E2E-test.
2. **Testnaam van 10 MB** (`tests/unit/test_overzichten_en_instellingen.py`, `@pytest.mark.parametrize("inhoud", …)` boven `test_ontbrekend_of_ongeldig_logo_toont_alleen_de_naam`). Ernst: laag.
   Zonder `ids` maakt pytest de test-ID van de inhoud. Bij een fout in het geval "groter dan 10 MB" schrijft pytest een regel van ruim 10 MB naar de uitvoer; dat gebeurde bij de mutant. Een CI-log of terminal loopt daarop vast. Herstel: `ids=["ontbreekt", "tekst", "svg", "gif", "te-groot"]`.
3. **Verwijzing in docstring** (`app/domein/instellingen.py:3`). Ernst: laag. Er staat `app.web.logo_laden`; de functie is `app.web.huisstijl.logo_laden`.

Geen bevinding over load: drie beheerders, het logo wordt per gunicorn-worker één keer in het geheugen geladen.

## Niet getest

- Een echte herstart van `web` met een vervangen bestand in `./huisstijl`; de unit-test bootst dat na met twee keer laden.
- De productie-compose zonder `compose.dev.yml` (`./huisstijl` leeg); het pad `FileNotFoundError` is wel unit-getest.
- Security van de route `/logo/<kenmerk>` en de verwerking van het bestand: dat beoordeelt aegis.

De werkmap is na afloop ongewijzigd voor de gestagede paden (`git diff --cached --stat`: 22 bestanden, 239 erbij, 144 eraf, gelijk aan het begin). `docs/business/intake.md` en `docs/product/backlog.md` staan tijdens de review als ongestaged gewijzigd; die wijziging komt niet van mij.

## Wat ging goed

De opdracht noemde de criteria, de bronnen en de exacte commando's, inclusief de mutant. Daardoor kon ik zonder zoeken per criterium een test aanwijzen. De stack draaide al met de nieuwe compose, dus er was geen herstart nodig.

## Wat kon beter

De suites en de migratieronde liepen op dezelfde lokale database als de draaiende stack. Dat ging goed omdat aegis niets draaide, maar een downgrade op de gedeelde database is voor anderen even zichtbaar.

## Wat deed ik zelf goed

De mutant draaide via een volume op één bestand (`-v <scratchpad>/huisstijl_mutant.py:/app/app/web/huisstijl.py:ro`), zodat de werkmap niet veranderde. De rechten heb ik vóór en na de migratieronde vastgelegd en met een diff vergeleken.

## Wat heb ik onderweg verbeterd

Bij de mutant bleek de uitvoer 10 MB groot door de test-ID. Daaruit kwam bevinding 2. Ik heb de uitvoer daarna alleen op de samenvattingsregel gelezen.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Een geparametriseerde test met binaire of grote invoer krijgt `ids=`." Zet in de opdracht voor een reviewer die een downgrade draait: "Draai de downgrade en upgrade op een eigen database (`nieuwe_database`) of meld vooraf aan de andere reviewers dat de gedeelde database even op de vorige revisie staat."
