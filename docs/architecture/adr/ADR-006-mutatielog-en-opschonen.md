# ADR-006 Mutatielog en opschonen

**Status:** Aanvaard, 2026-10-30
**Datum:** 2026-10-30
**Versie:** v1.8.0
**Stories:** BLB-024, BLB-025, BLB-026, BLB-033, BLB-034, BLB-043, BLB-047

## Context

Elke mutatie wordt gelogd en onder elk overzicht staat het log dat erbij hoort (intake, overlay §5). Het log bevat tijdstip, wie of wat de wijziging deed, wat er veranderde en waar relevant oud en nieuw, maar geen wachtwoorden, tokenwaarden, adressen, telefoonnummers of e-mailadressen (BLB-024). Beheerders kunnen het log niet wijzigen. Logregels worden na 5 jaar verwijderd, gerekend vanaf de mutatie. Gegevens van een oud-lid worden 5 jaar na de opzegdatum verwijderd, maar niet zolang het oud-lid nog een boot of plaats in de loods heeft. Geweigerde API-aanroepen komen ook in het log (BLB-033, BLB-034). Geslaagde aanroepen en wijzigingen in leden door de import komen er niet in; mutaties aan boten wel, ook als een import ze veroorzaakt (besluit stakeholder 2026-10-31). Sinds 2026-11-01 zijn er twee logs: de bootmutaties en het technische log (intake, Twee logs; BLB-043).

## Besluit

Er is één tabel `logregel`, alleen voor toevoegen. Daaruit komen twee logs.

| Veld | Inhoud |
|------|--------|
| tijdstip | Tijdstip met tijdzone |
| soort | `mutatie` of `api`; bepaalt niet in welk log de regel staat (zie Twee logs) |
| actor_soort, actor_id, actor_naam | Beheerder, token of taak; de naam wordt bij schrijven vastgelegd zodat hij blijft na het verwijderen van een account of token |
| actie | Vaste code, bijvoorbeeld `plaats.toegewezen`, `lid.bijgewerkt`, `token.geweigerd` |
| verwijzingen | Array van tekst als `plaats:12`, `rek:3`, `boot:40`, `lid:7` |
| gegevens | JSON met oud en nieuw, alleen voor velden die er mogen staan |

**Schrijven.** Alleen `domein/log` schrijft, aangeroepen vanuit elke wijzigende domeinfunctie in dezelfde transactie. Een lijst met verboden velden (adres, telefoon, e-mail, tokenwaarde; de sleutels blijven als vangnet, ook nu `lid` geen adres, telefoon of e-mail meer heeft) wordt bij schrijven gecontroleerd; bij die velden komt alleen "gewijzigd" in het log. Een lid staat in het log als verwijzing (`lid:7`), niet met naam. De opslag bevat die verwijzing en geen naam. Het log toont bij het tonen de naam van het lid zolang het lid bestaat (zie Leesbaar tonen); na het opschonen is het lid weg en toont het log de verwijzing zoals ze is (bouw slice 9, #174). Zo blijft na opschonen geen naam achter in logregels die nog niet 5 jaar oud zijn. De naam van een boot kan in jongere regels blijven staan; die is openbaar op de plaatspagina.

**Afscherming.** De applicatie heeft geen functie om logregels te wijzigen of te verwijderen. De database-gebruiker van de applicatie heeft op `logregel` alleen `INSERT` en `SELECT`. De opschoning draait in de worker met een aparte database-gebruiker die ook `DELETE` mag. Een fout in de webcode kan het log zo niet aantasten.

**Twee logs.** Er zijn twee logs (BLB-043, besluit stakeholder 2026-11-01). Het log van de bootmutaties bevat boot aangemaakt, gewijzigd of verwijderd, foto toegevoegd of vervangen, plaats toegewezen of vrijgegeven, een boot verplaatst (`boot.verplaatst`: één regel met de oude en de nieuwe plaats, onder beide plaatsen, de boot en het lid; issue #206), en een boot op de wachtlijst gezet of eraf gehaald (besluit stakeholder 2026-11-01, issue #41). Het technische log bevat de rest: tokens, geweigerde API-aanroepen, beheerders en inlogmethodes, instellingen, importverzoeken, de indeling (rekken en plaatsen aanmaken, wijzigen of verwijderen), de bootsoorten (`bootsoort.toegevoegd`, `bootsoort.hernoemd` met de oude en de nieuwe naam, `bootsoort.verwijderd`) en de opschoning. Beide staan in dezelfde tabel. De indeling hoort bij de actie en staat in `domein/log` (`BOOTMUTATIES`, `TECHNISCH`); een unittest faalt als een actie bij geen of bij beide hoort. Het veld `soort` blijft `mutatie` of `api` en bepaalt niet in welk log een regel staat. Het technische log toont alles wat geen bootmutatie is, ook acties die de code niet meer schrijft, en toont actie en verwijzing zoals opgeslagen (#174). Een wijziging van een plaats zelf (code, bootsoorten, clubplaats) staat dus in het technische log, niet onder de plaats. De actie `boot.gewijzigd` legt naam, bootsoort en eigenaar vast met oud en nieuw; bij een andere eigenaar verwijst de regel naar beide leden, en de eigenaar staat er met oud en nieuw als `lid:<id>` of `vereniging` in, zonder naam (issue #39).

**Tonen.** Elk scherm heeft een vaste filter, altijd binnen één log. Geen overzicht toont regels uit het technische log.

| Scherm | Log |
|--------|-----|
| `/log` | Alle bootmutaties |
| `/log/techniek`, eigen menuoptie | Het hele technische log |
| Boot | Bootmutaties met `boot:<id>` |
| Lid | Bootmutaties met `lid:<id>`, dus over de boten van dat lid |
| Plaats | Bootmutaties met `plaats:<id>` (toegewezen, vrijgegeven, verplaatst) |
| Boten | Bootmutaties van boten (`boot.`) |
| Vrije plaatsen | Toewijzen, vrijgeven en verplaatsen (`plaats.`, `boot.verplaatst`) |
| Wachtlijst | Handelingen op de wachtlijst (`wachtlijst.`); een kijker ziet dit scherm niet en ziet `wachtlijst.`-regels in geen enkel log |
| Opgezegd en opzeggend | Bootmutaties op de getoonde plaatsen |
| `/indeling`, `/rekoverzicht`, gebruikers, profiel, leden, instellingen | Geen log |

**Leesbaar tonen (BV-82, #174).** Alle schermen behalve `/log/techniek` tonen de actie en de verwijzingen als tekst; opslag en gegevens veranderen niet. De actie is de opgeslagen naam met punt en liggend streepje als spatie, in kleine letters (`plaats.toegewezen` wordt "plaats toegewezen"). Een eigen tekst per actie is niet nodig: de acties met een fout gespelde mechanische vorm (`bezetting.geimporteerd`, `indeling.geimporteerd`) staan alleen in het technische log, dat de opgeslagen namen toont. Een actie die niet in `BOOTMUTATIES` of `TECHNISCH` staat, blijft zoals opgeslagen. Een verwijzing wordt "Plaats B/2/2", "Boot <naam>", "Lid <naam> (<lidnummer>)", "Rek <naam>" (zonder tweede "Rek" als de naam er al mee begint), "Bootsoort <naam>", "Gebruiker <naam>" (voor `beheerder:<id>`) of "Token <naam>", gescheiden door ", ". Is het object verwijderd of de soort onbekend (`taakrun:5`, `clubboot`), dan blijft de opgeslagen verwijzing staan. De namen komen per pagina met één query per soort (`log.namen`) en zijn gebruikersinvoer: Jinja escapet ze. De gegevens (`bl-loggeg`) blijven zoals opgeslagen.

Elke beheerder ziet beide logs helemaal. Een kijker ziet geen van beide, alleen het log onder een scherm dat hij mag zien, zonder lidnummer. Een kijker ziet ook niet dat de eigenaar oud-lid is: vallen de regels `wachtlijst.toegevoegd` en `wachtlijst.verwijderd` helemaal weg (`log.zichtbaar`, besluit stakeholder op AEG-01), en de link "Meer in het log" vervalt. Een lid staat er als "Lid <naam>" (`log.namen` met `met_leden` uit). Een verwijzing `beheerder:<id>` heet voor iedereen "Gebruiker <naam>"; de acties `beheerder.rol_gewijzigd` en `beheerder.lid_gewijzigd` horen bij `TECHNISCH` (ADR-015). De acties van de wachtlijst staan in `BOOTMUTATIES` (slice 7): `wachtlijst.toegevoegd` met boot, bootsoort en aanmelddatum, en `wachtlijst.verwijderd` met boot, aanmelddatum en zo nodig een reden (`plaats toegewezen`, `oud-lid` of `andere eigenaar`). Beide verwijzen naar de boot en het lid. Krijgt een boot op de lijst een andere eigenaar, dan gaat hij van de lijst in dezelfde transactie als `boot.gewijzigd` (besluit stakeholder 2026-11-01); is de nieuwe eigenaar een oud-lid, dan is de reden `oud-lid`, ook als de eigenaar eerst onbekend was (besluit stakeholder 2026-11-17, issue #298). Haalt de import een boot van een oud-lid van de lijst, dan is het robottoken de actor (BLB-008, #27). Toewijzen geeft naast `plaats.toegewezen` een regel `wachtlijst.verwijderd` als de boot op de lijst stond. Een verwijderde boot gaat zonder eigen regel van de lijst; `boot.verwijderd` dekt dat. Een GIN-index op `verwijzingen` en een index op `tijdstip` houden de filters snel. Elk log toont de nieuwste 50 regels. `/log` en `/log/techniek` bladeren per 50 (`?pagina=`); een overzicht met 50 regels linkt naar `/log`, zonder zijn eigen filter (issue #42).

**Opschonen.** Een dagelijkse taak (ADR-007) doet in één transactie:

1. Logregels met een tijdstip van meer dan 5 jaar geleden verwijderen.
2. Kijkers verwijderen met een gekoppeld oud-lid, vóór de leden (ADR-015).
3. Oud-leden zoeken waarvan de startdatum (opzegdatum, of `uit_bron_op` als die ontbreekt, besloten door de stakeholder op 2026-10-30, architectuur §9 besluit 4) meer dan 5 jaar geleden ligt en waarvan geen boot een plaats heeft (besloten, besluit 3). De boten en foto's van het oud-lid gaan mee.
4. Van die oud-leden de boten, foto's en het lid zelf verwijderen.
5. Aantallen vastleggen in `taakrun` (taak `opschoning`: logregels, kijkers, leden, boten, foto's) en één logregel `opschoning.uitgevoerd` met alleen de aantallen en een verwijzing naar de run (BLB-026).

De grens rekent met `jaren_terug`: een startdatum van precies 5 jaar geleden blijft staan. Een opgeschoond oud-lid komt niet terug, want de import neemt een nieuw lid met een opzegdatum alleen op als die hooguit 5 jaar geleden is, met dezelfde grens (ADR-004 stap 4, issue #298). Dezelfde startdatum en grens bepalen of een oud-lid binnen de bewaartermijn valt en dus als eigenaar te kiezen is (BLB-005); de bouw zet die in één functie in `domein/leden` die opschoning, import en keuzelijst delen. De wachtlijst volgt de boot via de cascade. Foto's staan in de database (ADR-008), dus er blijft geen bestand op schijf achter. De opschoning gebruikt geen `FOR UPDATE`. De import kan een oud-lid weer actief maken. Daarom neemt de opschoning naast haar eigen slot ook het importslot; loopt er een import, dan wacht ze tot de volgende ronde van de worker (#49).

Sinds issue #298 geeft een beheerder een oud-lid binnen de bewaartermijn een boot, en een boot van een oud-lid een gewone plaats. Een oud-lid binnen de termijn valt niet onder de opschoning, dus dat botst niet, op één geval na. Wijst een beheerder een plaats toe aan een boot van een oud-lid buiten de termijn terwijl de opschoning loopt, dan heeft de opschoning het oud-lid al gekozen. Haar `DELETE` op die boot wacht op het slot van de toewijzing en raakt daarna een boot met een plaats. De verwijzing `plaats.boot_id` heeft geen `ON DELETE`, dus de database weigert die `DELETE`: de hele opschoning rolt terug, staat als mislukte run in `taakrun` en draait de volgende dag opnieuw, als de boot een plaats heeft en het oud-lid blijft staan (Probable; de bouw bevestigt dit met een test). Sinds het besluit van de stakeholder van 2026-11-17 (architectuur §10.2, vraag 11, ADR-003) krijgt een boot van een oud-lid buiten de termijn geen plaats. Toewijzen en opschoning rekenen met dezelfde functie en grens, dus dit geval blijft alleen over rond middernacht op de dag van de grens; dan faalt de opschoning veilig zoals hierboven. Verplaatsen raakt de opschoning niet, want de boot had al een plaats. Een `DELETE` op een boot die intussen een andere eigenaar kreeg, leest de rij opnieuw en slaat hem over. De code staat in `domein/opschonen`.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Logtabel per entiteit of SQLAlchemy-historie | Meer tabellen, geen gedeelde weergave onder overzichten |
| Databasetriggers die het log schrijven | Weten niet wie de actor is zonder sessievariabelen; regels voor verboden velden in SQL |
| Naam van het lid in de logregel | Blijft na opschonen van het lid nog jaren staan |
| API-aanroepen alleen naar stdout | Beheerders hebben geen serverrol en zouden geweigerde pogingen niet zien |
| Logregels pseudonimiseren in plaats van verwijderen | Termijn van 5 jaar is een besluit; verwijderen is eenvoudiger en volgt het besluit |
| Een tweede tabel voor het technische log | Dubbele afscherming en opschoning; een actie verhuist dan met een migratie in plaats van een regel in `domein/log` |

## Gevolgen

- Een nieuwe wijzigende functie zonder logregel valt op in de review en in een test die per domeinfunctie controleert dat er een regel bijkomt.
- Een nieuwe actie hoort bij precies één log; zonder indeling faalt de unittest. Ook `opschoning.uitgevoerd` (slice 9) komt in `TECHNISCH`.
- Een robot die elke minuut vraagt, geeft geen logregels; alleen weigeringen tellen mee.
- Back-ups bevatten verwijderde gegevens langer dan 5 jaar, tenzij hun bewaartermijn is afgestemd (architectuur §10, open vraag 1).

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.8.0 | 2026-11-20 | Opschoning van kijkers met een oud-lid; actie `beheerder.lid_gewijzigd` | Issue #353, besluiten stakeholder 2026-11-19 en 2026-11-20 |
| v1.7.2 | 2026-11-19 | Een kijker ziet geen wachtlijstregels in het log (tabel Tonen: Boot, Plaats, Boten en Vrije plaatsen tonen ze niet aan een kijker) | Besluit stakeholder op AEG-01, issue #322 |
| v1.7.1 | 2026-11-19 | Bouw van #322: reden `oud-lid` en "Meer in het log" verborgen voor een kijker; "Gebruiker" geldt voor elke lezer | Issue #322 |
| v1.7.0 | 2026-11-18 | Log voor een kijker, actie `beheerder.rol_gewijzigd` | ADR-015, issue #322 |
| v1.6.1 | 2026-11-17 | Toewijzen weigert een boot van een oud-lid buiten de termijn; het geval met de opschoning blijft alleen rond middernacht op de dag van de grens | Besluit stakeholder 2026-11-17, architectuur §10.2, vraag 11 |
| v1.6.0 | 2026-11-17 | Een beheerder geeft een oud-lid binnen de bewaartermijn een boot en een gewone plaats; import, opschoning en keuzelijst delen de grens; gelijktijdig toewijzen en opschonen faalt veilig op `plaats.boot_id` | Besluiten stakeholder 2026-11-16, issue #298 |
| v1.5.0 | 2026-11-14 | Leesbaar tonen van actie en verwijzing in de bootlogs; technisch log en opslag ongewijzigd; alinea Twee logs en tabel Tonen aangevuld | BV-82, issue #174 |
| v1.4.4 | 2026-11-13 | `boot.verplaatst` in `BOOTMUTATIES`; tabel Tonen (Plaats, Vrije plaatsen) en BLB-047 bij Stories | Issue #206 |
| v1.4.3 | 2026-11-10 | De grens van de opschoning staat los van de import; de import neemt geen nieuw opgezegd lid op | Issue #203 |
| v1.4.2 | 2026-11-09 | De opschoning kent de kolommen `adres`, `telefoon` en `email` niet meer; migratie 0018 schrijft een regel `token.ingetrokken` met actor systeem/migratie | Besluiten stakeholder 2026-11-08 en 2026-11-09, issue #180 |
| v1.4.1 | 2026-11-04 | Rekoverzicht toont geen log | Besluiten stakeholder 2026-11-04, issue #87 |
| v1.4.0 | 2026-11-03 | Acties van de bootsoorten in het technische log | Bouw slice 11, issue #56 |
| v1.3.1 | 2026-11-03 | De opschoning neemt het importslot: de import kan een oud-lid weer actief maken | Issue #49 |
| v1.3.0 | 2026-11-02 | Opschoning gebouwd; het log toont `lid:<id>` zonder naam, ook na opschonen; kopieën nagelopen | Bouw slice 9, issue #48 |
| v1.2.1 | 2026-11-02 | Reden `andere eigenaar` bij `wachtlijst.verwijderd` | Besluit stakeholder 2026-11-01, issue #43 |
| v1.2.0 | 2026-11-01 | Actienamen en gegevens van de wachtlijst; scherm Wachtlijst in de tabel | Bouw slice 7, issue #43 |
| v1.1.3 | 2026-11-01 | `boot.gewijzigd`: naam, bootsoort en eigenaar, eigenaar als verwijzing | Besluit stakeholder 2026-11-01, issue #39 |
| v1.1.2 | 2026-11-01 | Bladeren per 50 regels en link naar het log | Issue #42 |
| v1.1.1 | 2026-11-01 | Wachtlijstacties zijn bootmutaties | Besluit stakeholder 2026-11-01, issue #41 |
| v1.1.0 | 2026-11-01 | Twee logs: bootmutaties en techniek, indeling per actie, filter per scherm; rek en tokenoverzicht zonder log; wachtlijst open | Besluit stakeholder 2026-11-01, BLB-043, issue #38 |
| v1.0.0 | 2026-10-31 | Geslaagde API-aanroepen en wijzigingen in leden door de import niet in het log; versie en wijzigingslog toegevoegd | Besluit stakeholder 2026-10-31 (backlog vraag 20) |
