# ADR-004 Interface van de ledenbron en terugschrijven

**Status:** Aanvaard, 2026-10-30; herzien 2026-10-31 (integratiecontainer, ADR-012) en 2026-11-08 (e-boekhouden, issue #178)
**Datum:** 2026-10-30
**Versie:** v2.8.0
**Stories:** BLB-006, BLB-007, BLB-008, BLB-009, BLB-026

## Context

Leden worden niet in de applicatie beheerd maar dagelijks opgehaald uit e-boekhouden, en handmatig te starten (intake). De koppeling moet vervangbaar zijn door een andere bron. Er is een stub voor ontwikkeling en een bron voor e-boekhouden (issue #178). Terugschrijven van het aantal boten per bootsoort per lid staat standaard uit en gaat aan met een eigen schakelaar. Een lid dat uit de bron verdwijnt, wordt oud-lid en wordt niet verwijderd. Gegevens uit de bron zijn externe invoer (overlay §8). Sinds 2026-10-31 draait de koppeling in een aparte container die alleen via de API werkt (ADR-012).

## Besluit

De interface van de bron staat in de integratiecontainer (`integratie/`), niet in de applicatie. Hij heeft twee methoden, met per bron één klasse. De omgevingsvariabele `LEDENBRON` van de integratiecontainer kiest de klasse (`stub` of `eboekhouden`). Zonder waarde meldt de container dat er geen bron is en roept hij de API niet aan (BLB-007).

| Methode | Levert of vraagt | Gedrag |
|---------|------------------|--------|
| `haal_leden()` | Een lijst van bronrecords: lidnummer, naam, lid_sinds, opzegdatum | Gooit `LedenbronFout` bij een storing of een onleesbaar antwoord; de container meldt dat met `POST /api/v1/leden/import-mislukt` |
| `schrijf_bootaantallen(aantallen)` | Per lidnummer het aantal boten per bootsoort | De stub gooit `NietBeschikbaar`; e-boekhouden schrijft en geeft de aantallen geschreven, ongewijzigd, niet_gevonden en fout terug |
| `kan_terugschrijven` (eigenschap) | Ja of nee | Stub nee, e-boekhouden ja |

De bron doet alleen transport en vertaling naar het bronrecord. De container stuurt de volledige lijst met `PUT /api/v1/leden`. Validatie en opslag zitten in `domein/leden` achter de API, zodat elke bron en elke vervangende container dezelfde regels krijgt. Inloggegevens van de bron staan alleen in de omgeving van de integratiecontainer; de applicatie kent ze niet.

De import in `domein/leden` werkt in deze stappen, bij elke aanroep van `PUT /api/v1/leden`:

1. De lijst uit het verzoek nemen. Is het geen lijst, of zijn er meer dan 5000 records: 422, niets wijzigen. Een gemelde fout van de bron komt in `taakrun`, met een reden uit een vaste lijst (BLB-006).
2. Elk record valideren: lidnummer verplicht, tekstvelden ingekort tot een maximumlengte, datums geldig. Velden die het contract niet kent, zoals adres, telefoon en e-mail, worden genegeerd en niet bewaard (issue #180). Een ongeldig record wordt overgeslagen en geteld, zonder de inhoud te loggen.
3. Veiligheidsgrens: komen er minder dan de helft van het huidige aantal actieve leden terug, dan breekt de import af met 409 en staat hij als mislukte run in `taakrun`. Een kapotte bron of een container die een halve lijst stuurt, maakt zo niet alle leden oud-lid.
4. Records met een opzegdatum op of vóór vandaag die lokaal niet bestaan, worden overgeslagen en geteld als overgeslagen: een oud-lid dat nooit in de applicatie stond, komt er niet in (besluit stakeholder 2026-11-10, issue #203). Een opzegdatum in de toekomst komt wel binnen. Een bestaand lid dat opzegt, blijft staan met de opzegdatum, zodat zijn boot als boot van een oud-lid wordt herkend. Een opgeschoond oud-lid komt zo ook niet terug. Migratie 0020 verwijdert eenmalig de oud-leden zonder boot die al binnenkwamen; de koppelingen uit `naamkoppeling` gaan mee (ON DELETE CASCADE), logregels met `lid:<id>` blijven.
5. In één transactie: nieuwe leden aanmaken, gewijzigde bijwerken, leden die ontbreken krijgen `uit_bron_op` met de datum van vandaag. Boten van leden die oud-lid worden, gaan van de wachtlijst (BLB-008).
6. Wijzigingen in leden komen niet in het log; de aantallen staan in `taakrun`, in een run met taak `ledenimport`. Een mutatie in de botenadministratie die de import veroorzaakt, krijgt wel een logregel met het robottoken als actor (BLB-024, besluit stakeholder 2026-10-31).

De bron e-boekhouden (`koppeling/eboekhouden.py`, issue #178) logt in met `EBOEKHOUDEN_USERNAME`, `EBOEKHOUDEN_CODE1` en `EBOEKHOUDEN_CODE2` en vraagt met GetRelaties alle relaties op. De bron haalt eerst de spaties aan begin en eind van `Def2` weg en zet de waarde in kleine letters (issue #226, besluit van de stakeholder 2026-11-12). E-boekhouden vult het veld automatisch; dit vangt een tikfout op. Een relatie is een lid als `Def2` begint met "actief" (zoals `actief_gewoon`), of met "opgezegd" en `Def7` een opzegdatum heeft; "inactief" telt niet. Een relatie op "opgezegd" zonder opzegdatum slaat de bron over, ook bij het terugschrijven (issue #221). Was die relatie al lid, dan wordt het lid oud-lid zoals elk lid dat uit de bron verdwijnt. Het lidnummer is `Code`, de naam is `Bedrijf`, lid_sinds is `Def3` en de opzegdatum is `Def7`. Adres, telefoon en e-mail gaan niet mee en de applicatie bewaart ze niet (issue #180). De API leest een ontbrekend veld als leeg en overschrijft de bewaarde waarde. Een fout van e-boekhouden wordt `bron_geweigerd` (foutcode in het antwoord, HTTP 401 of 403), `bron_onbereikbaar` (geen verbinding, andere HTTP-fout) of `bron_onleesbaar` (geen geldig SOAP-antwoord); er gaat geen tekst van e-boekhouden naar de API of het log.

De stub in de integratiecontainer leest leden uit een JSON-bestand (`LEDENBRON_STUB_BESTAND`). De tests van de applicatie sturen het fixturebestand `tests/fixtures/leden.json` rechtstreeks naar `PUT /api/v1/leden`; dat is de nepbron.

Terugschrijven: de domeinlaag berekent de aantallen per lid per bootsoort, alleen voor boten met een toegewezen plaats en zonder clubboten (besluit stakeholder 2026-10-31); de vereniging rekent de contributie daarmee elders af per bootsoort; `GET /api/v1/bootaantallen` levert ze, uit één functie (`domein/boten.bootaantallen`, BLB-009). De instelling "terugschrijven" in de applicatie vervalt. In de integratiecontainer schrijft `schrijf_bootaantallen` van de bron e-boekhouden na elke geslaagde import, en alleen als `BOOTAANTALLEN_SCHRIJVEN=aan` staat (standaard `uit`; `aan` zonder deze bron weigert de container bij het starten). Per lid wordt het record vers opgehaald (GetRelaties) en met alleen `Def10` gewijzigd teruggestuurd (UpdateRelatie), als JSON-tekst met `ensure_ascii=False` en de sleutels zoals de API ze geeft. Een gelijke waarde wordt niet geschreven, een onbekend lidnummer wordt overgeslagen en geteld, en na drie fouten achter elkaar stopt het schrijven. Er is geen herhaling: de volgende poging is de volgende geslaagde import. Het record verlaat de container niet en komt niet in het log.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Plug-insysteem met entry points | Eén vereniging per installatie; een eigen container of een keuze in de omgeving volstaat |
| Bron schrijft direct in de database | Validatie en log per bron dubbel; een fout in een bron raakt de gegevens |
| Leden die verdwijnen verwijderen | In strijd met de intake |
| Terugschrijven nu al bouwen achter een vlag | Vervallen op 2026-11-08: de stakeholder koos voor bouw met een schakelaar die standaard uit staat; de live proef op een testrelatie volgt apart |

## Gevolgen

- Een nieuwe bron is één klasse en een waarde voor `LEDENBRON` in de integratiecontainer, of een eigen container met de aanroepen uit ADR-012. Aegis beoordeelt de echte e-boekhoudenkoppeling vóór de commit.
- De oud-ledenstatus is afgeleid uit opzegdatum en `uit_bron_op`; verdwijnt een lid zonder opzegdatum uit de bron, dan telt de datum waarop de synchronisatie het lid niet meer vond als opzegdatum (besloten door de stakeholder, 2026-10-30, architectuur §9 besluit 4).
- De veiligheidsgrens kan een echte massale opzegging tegenhouden. Bij 210 leden is dat onwaarschijnlijk; de beheerder ziet de afbreking op de statuspagina.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v2.8.0 | 2026-11-10 | Bron e-boekhouden slaat een relatie op "opgezegd" zonder opzegdatum (`Def7`) over | Besluit stakeholder 2026-11-10, issue #221 |
| v2.7.0 | 2026-11-10 | Stap 4: een nieuw lid met een opzegdatum op of vóór vandaag wordt niet aangemaakt; migratie 0020 ruimt oud-leden zonder boot op | Besluit stakeholder 2026-11-10, issue #203 |
| v2.6.0 | 2026-11-09 | De lidpagina toont de aantallen per bootsoort niet meer; alleen de API levert ze | Besluit stakeholder 2026-11-08, issue #179 |
| v2.5.0 | 2026-11-09 | Kolommen `adres`, `telefoon` en `email` van `lid` vervallen (migratie 0018); de import negeert die velden | Besluiten stakeholder 2026-11-08 en 2026-11-09, issue #180 |
| v2.4.0 | 2026-11-08 | Bron e-boekhouden met zeep, velden, redenen; terugschrijven naar `Def10` achter `BOOTAANTALLEN_SCHRIJVEN` (standaard uit) | Besluiten stakeholder 2026-11-08, issue #178 |
| v2.3.0 | 2026-11-02 | Bootaantallen gebouwd, één telling voor lijst per lid en API | Bouw slice 9, issue #48 |
| v2.2.1 | 2026-10-31 | Bootaantallen alleen voor boten met een plaats, zonder clubboten | Besluit stakeholder 2026-10-31 |
| v2.2.0 | 2026-10-31 | Taak `ledenimport` in `taakrun`; de afbreking door de veiligheidsgrens is een mislukte run | Issue #22, bouw slice 6 |
| v2.1.0 | 2026-10-31 | Geen logregels voor wijzigingen in leden; een gemelde fout alleen in `taakrun` | Besluit stakeholder 2026-10-31 (backlog vraag 20) |
| v2.0.0 | 2026-10-31 | De bron draait in de integratiecontainer; de synchronisatie start met `PUT /api/v1/leden`; instelling "terugschrijven" vervalt | Besluiten stakeholder 2026-10-31, ADR-012 |
| v1.0.0 | 2026-10-30 | Eerste versie | |
