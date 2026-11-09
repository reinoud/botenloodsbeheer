# ADR-012 Integratiecontainer en interne API

**Status:** Besloten door Foundation (besluiten stakeholder 2026-10-31)
**Datum:** 2026-10-31
**Versie:** v1.9.0
**Stories:** BLB-006, BLB-007, BLB-008, BLB-009, BLB-029 tot en met BLB-035, BLB-037

## Context

Een aparte, vervangbare container doet alle imports en exports: leden ophalen en het aantal boten per lid en per bootsoort terugschrijven. Hij praat alleen met de API, over het interne netwerk van compose. De API staat standaard aan, is niet vanaf internet bereikbaar en heeft als standaardwhitelist het interne netwerk (intake, besluiten 2026-10-31). Terugschrijven staat standaard uit (overlay §5) en gaat aan met `BOOTAANTALLEN_SCHRIJVEN` (issue #178).

## Besluit

**Containers en netwerken.** Er komen twee diensten bij. `api` draait het applicatie-image met `DIENST=api` en alleen de blueprint `/api/v1`, die `web` niet meer registreert. Alleen de rol `botenloods_api` maakt leden aan en werkt ze bij; `web` houdt leesrecht op `lid`. In `taakrun` ziet en wijzigt `botenloods_api` alleen de rijen met taak `ledenimport` of `bootaantallen`: een rijbeleid (migratie 0014) houdt hem weg bij de hartslag van de worker. `integratie` is een eigen image uit `integratie/`, zonder applicatiecode.

| Netwerk | Leden | Eigenschap |
|---------|-------|-----------|
| `voorkant` | Traefik, web, api | `internal`, extern aangemaakt (ADR-013) |
| `achterkant` | web, api, worker, migrate, db | `internal: true` |
| `koppeling` | Traefik, integratie | `internal`, extern aangemaakt, vast subnet `KOPPELNET` (standaard `10.203.0.0/24`) |
| `buiten` | integratie | Uitgaand verkeer naar e-boekhouden |

Traefik heeft een niet gepubliceerd entrypoint `intern` op poort 8081, met een router die alleen `/api/v1/` vanaf `KOPPELNET` doorstuurt naar `api` (ADR-013). Het entrypoint op 443 kent geen route naar `api`. Zo gelden de rate limits en het vastgestelde clientadres uit ADR-005, en bereikt `integratie` `api` en `db` niet rechtstreeks.

Wie de API op internet wil, voegt bewust `compose.api-extern.yml` toe (BLB-042, ADR-013).

**Aanroepen.** Het contract staat in `app/api/openapi.yaml` en kent vijf aanroepen voor de integratiecontainer; meer gebruikt hij niet. Alle vijf zijn gebouwd; `GET /api/v1/bootaantallen` kwam met BLB-009 in slice 9 (backlog vraag 21). De rol `botenloods_api` leest daarvoor ook `plaats` en `bootsoort` (migratie 0008). De meegeleverde container roept hem aan na een geslaagde import, als `BOOTAANTALLEN_SCHRIJVEN=aan` staat.

| Aanroep | Recht | Argumenten | Terugkeerwaarde |
|---------|-------|------------|-----------------|
| `GET /api/v1/ik` | elk geldig token | geen | 200 `{"token": naam, "rechten": [...], "verloopt_op": datum}` |
| `GET /api/v1/leden/importverzoek` | `leden:importeren` | geen | 200 `{"aangevraagd": true}` of `{"aangevraagd": false}` |
| `PUT /api/v1/leden` | `leden:importeren` | `{"leden": [record, ...]}`, altijd de volledige lijst; record: `lidnummer`, `naam`, `lid_sinds`, `opzegdatum` (datums `JJJJ-MM-DD`) | 200 `{"ontvangen", "nieuw", "bijgewerkt", "uit_bron", "ongeldig", "overgeslagen"}`; 409 bij de veiligheidsgrens of een lopende import; 413 boven 2 MB; 422 als `leden` geen lijst is of meer dan 5000 records heeft |
| `POST /api/v1/leden/import-mislukt` | `leden:importeren` | `{"reden": ...}`, één van `bron_onbereikbaar`, `bron_onleesbaar`, `bron_geweigerd` | 201; andere reden 422 |
| `GET /api/v1/bootaantallen` | `bootaantallen:lezen` | geen | 200 `[{"lidnummer", "aantallen": {bootsoort: aantal}}]`, voor elk lid elke bootsoort, ook 0 |

**Leesaanroepen (slice 10).** Vier aanroepen voor persoonlijke tokens en andere koppelingen; de integratiecontainer gebruikt ze niet. Elke aanroep geeft de hele lijst, zonder filters of paginering: bij 160 plaatsen, 180 boten en 210 leden blijft een antwoord ruim onder 100 kB. De domeinlaag kiest de velden. Een veld zonder waarde is `null`. Adres, telefoon en e-mail van leden bestaan niet meer (issue #180); het recht `persoonsgegevens` is vervallen.

| Aanroep | Recht | Velden per element |
|---------|-------|--------------------|
| `GET /api/v1/plaatsen` | `plaatsen:lezen` | `code`, `rek`, `clubplaats`, `bootsoorten`, `boot` (`{"id", "naam"}`) |
| `GET /api/v1/boten` | `boten:lezen` | `id`, `naam`, `bootsoort`, `plaats` (code), `eigenaar` (`{"lidnummer", "naam"}`, `null` bij een clubboot) |
| `GET /api/v1/leden` | `leden:lezen` | `lidnummer`, `naam`, `oud_lid`, `lid_sinds`, `opzegdatum` (besluit 2026-11-09: mee met `leden:lezen`) |
| `GET /api/v1/wachtlijst` | `wachtlijst:lezen` | `bootsoort`, `boot` (`{"id", "naam"}`), `eigenaar` (als bij boten), `aangemeld_op` |

`oud_lid` komt uit `is_oud_lid`. Foto en publieke sleutel staan er niet in. Volgorde: plaatsen zoals in het overzicht, boten op naam, leden op lidnummer, wachtlijst per bootsoort op `aangemeld_op`. De paden hebben geen parameter of querystring, dus de toegangslog verandert niet. `botenloods_api` krijgt leesrecht op `rek` en `plaats_bootsoort` (migratie 0009, ADR-005).

**Regels aan de kant van de API.** `PUT /api/v1/leden` roept `domein/leden.importeer` aan met de ontvangen lijst. Alle regels uit ADR-004 gelden daardoor ongewijzigd: validatie per record zonder de inhoud te loggen, de veiligheidsgrens van de helft, geen nieuw lid met een opzegdatum van meer dan 5 jaar geleden, `uit_bron_op` voor een lid dat in de lijst ontbreekt, en boten van oud-leden van de wachtlijst. Wijzigingen in leden komen niet in het log; mutaties aan boten wel (ADR-004 v2.1.0). Een advisory lock voorkomt twee imports tegelijk. Een geslaagde import, een import die de veiligheidsgrens tegenhoudt (409) en een gemelde fout zijn een run in `taakrun` met taak `ledenimport`; een open verzoek van een beheerder krijgt die uitkomst. Een 413, een 422 en een 409 omdat er al een import loopt, laten `taakrun` ongemoeid: er is dan niets geïmporteerd. De reden bij een fout komt uit een vaste lijst, zodat geen tekst van buiten op de statuspagina komt. De blueprint `/api/v1` is vrijgesteld van CSRF (`csrf.exempt`): de API gebruikt alleen het token in de header en geen cookie, dus een andere site kan geen aanroep doen namens een ingelogde beheerder. De applicatie geeft boven 2 MB de 413 als JSON (`MAX_CONTENT_LENGTH`); Traefik weigert boven 3 MB als buitengrens (ADR-013).

**Integratiecontainer.** Een lus van 60 seconden: vraag het importverzoek op, en importeer bij een verzoek of na `SYNC_TIJDSTIP` als die dag nog geen import slaagde. Na een fout hooguit één geplande poging per uur; een verzoek van een beheerder wacht niet (besluit stakeholder 2026-10-31, #28), behalve na een fout van de API zelf (elke HTTP-fout behalve 409, en een netwerkfout): dan blijft het verzoek open en komt een geweigerde aanroep in het log van de API. Na een fout van de bron of een 409 is het verzoek gesloten. Een nieuw token in het secretbestand heft die wachttijd op, zodat een vervangen token direct werkt (BLB-039 criterium 3). Een lijst van meer dan 5000 records of meer dan 2 MB stuurt de container niet; hij meldt dan `bron_onleesbaar`. De bron zit achter de interface uit ADR-004 (`haal_leden`, `schrijf_bootaantallen`), met een stub die een JSON-bestand leest en een bron voor e-boekhouden. Na een geslaagde import en alleen met `BOOTAANTALLEN_SCHRIJVEN=aan` vraagt de container `GET /api/v1/bootaantallen` op en schrijft de bron per lid `Def10`; een fout daarbij maakt de import niet mislukt en wordt niet herhaald, en de container logt één regel met aantallen. De container draait zonder root en alleen-lezen.

**Bibliotheek en image (issue #178).** De aanroepen naar de API gebruiken alleen de standaardbibliotheek. De bron e-boekhouden gebruikt `zeep` (met `requests`, `lxml` en de overige afhankelijkheden), vastgepind met hashes in `integratie/requirements.txt` (uit `requirements.in`, met `uv pip compile` en `exclude-newer` zoals het project). Het image heeft drie stages: pip installeert in `bouw` met `--require-hashes` en `--only-binary :all:` naar `/pakketten`, `test` voegt de testpakketten toe, en het eindimage kopieert alleen `/pakketten` uit `bouw` en verwijdert pip (#59). Dependabot volgt `/integratie` met het ecosysteem `pip`. `eboekhouden-python` is niet gekozen: de bibliotheek kan een relatie niet bijwerken. De WSDL van e-boekhouden staat als kopie in het image (`koppeling/eboekhouden.wsdl`) en wordt dus niet bij het starten opgehaald: de container start zonder netwerk, de dienst bepaalt zijn eigen interface niet tijdens het draaien, en de alleen-lezen container hoeft niets te cachen. Verandert e-boekhouden de interface, dan wordt de kopie vervangen. De WSDL noemt een http-adres; de bron gebruikt vast `https://soap.e-boekhouden.nl/soap.asmx`, zodat de inloggegevens niet onversleuteld verzonden worden. Het adres is geen instelling. De tests met zeep draaien in `tests/integratie` in een testdoel van hetzelfde Dockerfile; zeep staat niet in het applicatie-image.

**Token en aanmelden.** De integratiecontainer krijgt een robottoken met alleen `leden:importeren` en `bootaantallen:lezen`. Het eerste token ontstaat met de CLI in `web`: `flask token robot <naam> --recht ... [--whitelist CIDR] [--dagen N]`. De whitelist is standaard `KOPPELNET`, de geldigheid standaard 365 dagen en hooguit 3 jaar. De CLI toont het token één keer en schrijft een logregel met actor `cli`. Intrekken kan met `flask token intrekken <naam>`, ook met een logregel; vervangen is een nieuw token maken en het oude intrekken. De beheerder zet het in `secrets/api_token` (mode 0600); compose levert dat als secret op `/run/secrets/api_token` (`API_TOKEN_FILE`). Compose start niet zonder dat bestand. De installatie maakt het daarom leeg aan (`install -m 600 /dev/null secrets/api_token`), en een leeg bestand geldt als "zonder token". Op Linux moet gebruiker 10001, waaronder de container draait, het bestand kunnen lezen (`chown 10001`). De container leest het bij elke run opnieuw, dus een nieuw token vraagt geen herstart. Zonder token meldt de container dat in zijn log en wacht een minuut.

**Beheerdocumentatie.** Forge schrijft `documentatie/beheer/integratiecontainer.md`: token maken en instellen, de aanroepen met voorbeeldcode (de vijfde vanaf slice 9), en wat een eigen container moet doen.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| API in `web`, met een blokkade op `/api/` in de proxy | `web` staat aan internet en zou leden mogen schrijven; de scheiding in de database verdwijnt |
| Integratiecontainer rechtstreeks naar `api:8000` | Geen rate limit en een clientadres dat de whitelist niet betrouwbaar maakt |
| Import per lid (`POST` en `PATCH`) | Een verdwenen lid is dan niet te herkennen, en de veiligheidsgrens werkt niet |

## Gevolgen

- `app/ledenbron/` en de synchronisatie in de worker verdwijnen (ADR-004, ADR-007).
- Er zijn vier databaserollen: eigenaar, web, api en taken. `integratie` heeft geen databaserol.
- Een vervangende container kent alleen de aanroepen uit het contract; een halve lijst houdt de veiligheidsgrens tegen.
- Na een handmatig verzoek begint de import binnen een minuut.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.9.0 | 2026-11-09 | Leesaanroepen zonder `persoonsgegevens`; lid sinds en opzegdatum mee met `leden:lezen`; `PUT /leden` kent adres, telefoon en e-mail niet meer en negeert ze; contract 0.9.0 | Besluiten stakeholder 2026-11-08 en 2026-11-09, issue #180 |
| v1.8.0 | 2026-11-08 | Bron e-boekhouden met zeep, hashes en een image in drie stages; terugschrijven achter `BOOTAANTALLEN_SCHRIJVEN`; WSDL als kopie in het image | Besluiten stakeholder 2026-11-08, issue #178 |
| v1.7.0 | 2026-11-05 | Rijbeleid op `taakrun` voor `botenloods_api` | Issue #24, veiligste eenvoudige variant |
| v1.6.0 | 2026-11-03 | Vier leesaanroepen; `compose.api-extern.yml` komt met BLB-042 | Ontwerp slice 10, issue #51 |
| v1.5.0 | 2026-11-02 | Vijfde aanroep gebouwd | Bouw slice 9, issue #48 |
| v1.4.0 | 2026-10-31 | Traefik in plaats van Nginx: netwerken, entrypoint `intern`, grens van 2 MB in de applicatie | Besluit stakeholder 2026-10-31, issue #29 (ADR-013) |
| v1.3.1 | 2026-10-31 | Een verzoek van een beheerder wacht na een fout niet het uur af, behalve na een fout van de API zelf | Besluit stakeholder 2026-10-31, issue #28 |
| v1.3.0 | 2026-10-31 | Gelijk aan de bouw van slice 6: vier aanroepen gebouwd, de vijfde in slice 9; `domein/leden.importeer`; uitkomsten in `taakrun` (taak `ledenimport`); secretbestand leeg aanmaken en uid 10001; nieuw token heft de wachttijd op; grens van 5000 records en 2 MB in de container; CSRF-vrijstelling van `/api/v1`; Nginx tot 2 MB | Issue #22 |
| v1.2.0 | 2026-10-31 | Geen logregel per lid | Besluit stakeholder 2026-10-31 (backlog vraag 20) |
| v1.1.0 | 2026-10-31 | Robottoken intrekken met de CLI (backlog vraag 17) | Besluit regie, veiligste eenvoudige variant |
| v1.0.0 | 2026-10-31 | Eerste versie | Besluiten stakeholder 2026-10-31 |
