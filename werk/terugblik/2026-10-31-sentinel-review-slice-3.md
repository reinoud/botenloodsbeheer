# Terugblik sentinel: review slice 3 (issue #13)

Datum: 2026-10-31. Taak: review van de gestagede wijziging van slice 3 op tests, dekking en de suites.

## Oordeel

Akkoord. Er is geen bevinding met ernst hoog of middel. Vier punten met ernst laag staan hieronder. Ze blokkeren de commit niet.

## Testaantallen

| Suite | Geslaagd | Mislukt | Errors | Overgeslagen |
|-------|----------|---------|--------|--------------|
| Unit (`run --rm test`) | 216 | 0 | 0 | 0 |
| Unit met `-W error::ResourceWarning` | 216 | 0 | 0 | 0 |
| E2E (`tests/e2e/draai.sh`, 4 bestanden) | 13 | 0 | 0 | 0 |
| E2E los: `test_overzichten.py -k huisstijl` | 1 | 0 | 0 | 0 (2 niet geselecteerd) |

Mutanten zijn als volume over het bestand in de testcontainer gezet. De werkmap is niet gewijzigd: `git diff --cached --stat` geeft nog 27 bestanden, 947 regels erbij en 38 eraf. Een niet-gestagede wijziging in `docs/architecture/adr/ADR-002-frontendaanpak.md` en `docs/PROJECT-OVERLAY.md` komt niet van mij.

## Dekking per criterium

| Criterium | Test |
|-----------|------|
| BLB-015 c1: alleen vrije plaatsen, met rek, code en bootsoorten, zonder clubplaatsen | unit `test_vrije_plaatsen_zonder_bezet_en_clubplaats`, `test_vrije_plaatsen_scherm_met_filter_en_vrijgeven` |
| BLB-015 c2: filter surfski | dezelfde unittests; E2E `test_vrije_plaatsen_indeling_op_telefoon_en_export` |
| BLB-015 c3: melding zonder vrije plaats | unit `test_vrije_plaatsen_scherm_met_filter_en_vrijgeven` (supboard) |
| BLB-011 c2: vrijgegeven plaats in de lijst | unit `test_vrije_plaatsen_scherm_met_filter_en_vrijgeven` |
| BLB-003 c1: clubplaats niet bij de vrije plaatsen | unit (A03), E2E (clubplaats niet zichtbaar na filter) |
| BLB-016 c1: per rek code, status, boot en eigenaar | unit `test_indeling_toont_status_boot_en_eigenaar` |
| BLB-016 c2: plaats opent het plaatsdetail | unit (href), E2E (klik naar "Plaats ...") |
| BLB-016 c3: telefoon zonder zijwaarts scrollen | E2E (360 px, `scrollWidth <= innerWidth`) |
| BLB-019 c1: boten met bootsoort en plaats of "geen plaats" | unit `test_lid_met_boten_en_plaats`; deel wachtlijst niet gedekt (verschoven) |
| BLB-019 c2: zoeken op naam of lidnummer | unit `test_leden_zoeken_op_naam_of_lidnummer` (ook `%` en `_`); E2E `test_lid_zoeken_en_plaatsen_van_opgezegde_leden` |
| BLB-018 c1: rek, code, boot, naam, opzegdatum, oudste bovenaan | unit `test_plaatsen_van_oud_leden_oudste_eerst`, `test_geen_plaatsen_van_oud_leden`; E2E (sortering) |
| BLB-018 c2: vanuit de lijst vrijgeven | E2E (knop "Plaats ... vrijgeven" op het plaatsdetail) |
| BLB-017 c1: rij per plaats met de 7 kolommen | unit `test_export_kolommen_en_geen_contactgegevens` |
| BLB-017 c2: geen adres, telefoon, e-mail of foto | dezelfde unittest (ook `_images`); E2E (XML in het bestand) |
| BLB-017 formule-injectie | unit `test_export_maakt_geen_formule_van_een_naam` |
| BLB-027 c1: naam, kleuren en logo op alle pagina's, ook openbaar | unit `test_opslaan_met_log_en_overal_zichtbaar`, `test_logo_opslaan_vervangen_en_tonen`; E2E `test_huisstijl_instellen_en_terugzetten` (kleur en logo als bezoeker); deel kaartjes niet gedekt (verschoven) |
| BLB-027 c2: ongeldig logo geweigerd, oud logo blijft | unit `test_ongeldig_logo_geweigerd_en_oude_blijft` (tekst, SVG, GIF); E2E |
| BLB-027 c3: waarschuwing bij slecht contrast | unit `test_slecht_contrast_geeft_waarschuwing_maar_slaat_op`, `test_contrast_volgens_wcag`; E2E |
| BLB-027 c4: neutrale standaard | unit `test_neutrale_standaard_zonder_instellingen`, `test_ongeldige_kleur_in_database_wordt_standaard` |
| Mutatielog bij instellingen | unit (`instelling.gewijzigd`, `instelling.logo_toegevoegd`); `instelling.logo_vervangen` niet expliciet |
| Recente inlog op beide POST-routes (ADR-001) | unit `test_recente_inlog_vereist` |
| Inloggen vereist op de nieuwe schermen | unit `test_schermen_vragen_inloggen`, `test_export_vraagt_inloggen`, `test_bezoeker_wijzigt_geen_instellingen` |

## Verschuivingen

Beide verschuivingen kloppen. Er is nog geen wachtlijst in het datamodel (`app/models.py` kent geen wachtlijst) en backlog §5 zet BLB-013 en BLB-014 in slice 4. Het issue noemt BLB-008 c3 en BLB-011 c3 als afhankelijke criteria; dat volgt de briefingchecklist. De kaartjes zijn BLB-021 in slice 5; BLB-021 hangt volgens de backlog af van BLB-027, dus de volgorde past.

## Racetest en mutanten

Drie mutanten van `_vergrendel` in `app/domein/instellingen.py:178-179`, met de racetest los gedraaid:

| Mutant | Uitkomst |
|--------|----------|
| zonder `populate_existing` | faalt (SAWarning: DELETE op afbeelding, 0 rijen) |
| zonder `with_for_update` | faalt, 3 van 3 keer, met dezelfde SAWarning |
| zonder beide | faalt |

De uitleg van forge in het issuecomment klopt niet. Forge meldt dat de test zonder `FOR UPDATE` slaagt omdat `INSERT ... ON CONFLICT DO NOTHING` op de vergrendelde rij wacht. In deze run wacht de INSERT niet: een rij die alleen met `FOR UPDATE` is vergrendeld en niet gewijzigd, geldt voor de INSERT als bestaand conflict. De tweede sessie loopt dan door, leest de oude waarde en blokkeert pas bij de UPDATE van de rij. Daarna verwijdert ze een logo dat al weg is. De test vangt dus beide vergrendelingen af. De code is goed; alleen de toelichting in het issue en in de terugblik van forge moet worden rechtgezet.

## NullPool in migrations/env.py

Dit is de juiste oplossing. Met de oude `env.py` (uit HEAD) en `-W error::ResourceWarning` gaf de unitsuite herhaaldelijk "psycopg.Connection ... was deleted while still open". De engine in `env.py` hield verbindingen in zijn pool vast tot de garbage collector ze opruimde, soms midden in een latere test. Met NullPool zijn die meldingen weg. NullPool is ook wat het standaardsjabloon van Alembic gebruikt, en een migratie draait eenmalig, dus er is geen nadeel voor de uitrol. Zonder `-W` slaagde de suite met de oude `env.py` deze keer ook: de error hangt af van het moment waarop de garbage collector draait.

## Migratie

Er is geen migratie nodig en er is er geen gestaged: `migrations/versions/` en `app/models.py` zijn niet gewijzigd. De CHECK-constraint op `afbeelding.soort` laat `logo` al toe (`0002_slice_1b_indeling_leden_boten.py:32`). De routes bestaan volgens `url_map` in de webcontainer.

## Bevindingen (alle ernst laag)

1. `tests/unit/test_overzichten_en_instellingen.py:294`: `@pytest.mark.filterwarnings("error")` maakt van elke waarschuwing een fout, ook van een ResourceWarning die een andere test achterlaat. Zo ontstond de error die de regie met NullPool heeft opgelost. Voorstel: `@pytest.mark.filterwarnings("error::sqlalchemy.exc.SAWarning")`. Een mutant zonder `populate_existing` levert juist die SAWarning op, dus de test blijft hem vangen.
2. Issuecomment #13 en `werk/terugblik/2026-10-31-forge-slice-3.md`: de bewering dat de racetest zonder `FOR UPDATE` slaagt, klopt niet (zie Racetest en mutanten). Zet de tekst recht.
3. `app/web/templates/opgezegd.html:10` en `:18`: de kolom heet "Opgezegd op", maar toont volgens `app/domein/indeling.py:62-65` ook de dag waarop een lid uit de bron verdween. Dat is geen fout. Wel kan het een beheerder verwarren; voorleggen aan apex (bijvoorbeeld "Oud-lid sinds").
4. Definition of done, "betrokken ADR's bijgewerkt": ADR-002 staat niet in de gestagede wijziging. Er ligt nu een niet-gestagede wijziging in `docs/architecture/adr/ADR-002-frontendaanpak.md`. Neem die mee in de commit of in een aparte documentatiecommit.

Kleine observaties zonder actie: `instelling.logo_vervangen` als logactie is niet apart getest, alleen `instelling.logo_toegevoegd`. Aan het eind van de suite meldt Python nog een "unclosed file <_io.BufferedRandom>" (een tijdelijk bestand, vermoedelijk van een upload in een test); dat geeft geen fout. Het logo dat de E2E-test uploadt, blijft in de ontwikkelstack staan, zoals de test zelf meldt.

## Wat ging goed

De tests volgen de criteria bijna één op één, met unhappy flows (SVG, GIF, `%` en `_` in de zoektekst, formule in een naam, recente inlog). De E2E-test voor de huisstijl zet de instellingen in een `finally` terug. Beide suites slaagden in één keer.

## Wat kon beter

Forge testte de mutant zonder `FOR UPDATE` en kwam tot een andere uitkomst dan ik. Hoe forge de mutant maakte, staat niet in het issue, dus ik kon het verschil niet nagaan.

## Wat deed ik zelf goed

Ik heb de mutanten als volume over het bestand in de testcontainer gezet, zodat de werkmap niet veranderde terwijl aegis tegelijk las. De mutant zonder `FOR UPDATE` heb ik drie keer gedraaid voordat ik de uitleg van forge tegensprak. Voor NullPool heb ik de oude `env.py` met `-W error::ResourceWarning` gedraaid, zodat het effect zichtbaar was ondanks de wisselende timing.

## Wat heb ik onderweg verbeterd

Mijn eerste extractie van de stories met awk ging mis; ik ben overgestapt op een kort Python-script. De eerste mutantrun liet geen samenvatting zien door een te ruime grep; die heb ik aangescherpt.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: een agent die meldt dat een mutant overleeft, noemt de exacte diff van die mutant en het commando, zodat de reviewer hetzelfde kan draaien.

Zet in de opdracht: een test met `filterwarnings("error")` noemt de categorie van de waarschuwing, zodat waarschuwingen uit andere tests hem niet laten falen.

Zet in de opdracht: een reviewer draait mutanten via een volume over het bestand in de testcontainer (`run --rm -v <scratchpad>/<mutant>.py:/app/<pad>:ro test`), niet in de werkmap.
