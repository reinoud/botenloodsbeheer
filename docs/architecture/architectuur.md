# Architectuur botenloodsbeheer

**Project:** botenloodsbeheer
**Versie:** v0.3.0
**Datum:** 2026-10-31
**Opgesteld door:** Foundation, Principal Architect
**Status:** Concept, besluiten van de stakeholder verwerkt (2026-10-30 en 2026-10-31)
**Bronnen, in volgorde van gezag:** `docs/business/intake.md` (inclusief de besluitensecties van 2026-10-30 en 2026-10-31), `docs/PROJECT-OVERLAY.md`, `docs/product/backlog.md` v0.1.0.

## 1. Samenvatting

Botenloodsbeheer is één Flask-applicatie met één PostgreSQL-database, voor één vereniging per installatie. Het ontwerp is bewust klein: 160 plaatsen, 210 leden en 3 beheerders vragen geen services, wachtrij, cache of frontend-build. De webinterface is server-rendered. De API is een tweede ingang op dezelfde domeinlaag, in een eigen container die alleen over het interne netwerk bereikbaar is. Imports en exports van leden doet een aparte, vervangbare integratiecontainer die alleen de API gebruikt (ADR-012). Opschonen en de heartbeat draaien in een workercontainer van hetzelfde image.

De drie keuzes met de meeste gevolgen zijn: beheerders loggen in met een passkey of met een wachtwoord plus TOTP (ADR-001, besluit van de stakeholder), een plaats heeft een vaste openbare sleutel los van de plaatscode zodat de QR-code blijft werken (ADR-003), en elke bedrijfsregel staat op één plek in de domeinlaag, die zowel de webinterface als de API gebruikt.

**Architectuurgezondheid:** Sound. De besluiten van de stakeholder van 2026-10-30 en 2026-10-31 zijn verwerkt (§9).

## 2. Containers

De installatie bestaat uit zes containers in één `docker-compose.yml`, verdeeld over vier netwerken (ADR-012). Ze draaien alle zes zonder root.

| Container | Inhoud | Taak | Bereikbaar van buiten |
|-----------|--------|------|-----------------------|
| `nginx` | Nginx (officieel image, unprivileged-variant) | TLS (vaste domeinnaam met HTTPS, §9 besluit 2), beveiligingsheaders, rate limiting, maximale uploadgrootte; publieke server naar `web`, interne server op poort 8081 naar `api` | Ja, poort 443 (en 80 voor doorverwijzing); 8081 niet |
| `web` | Applicatie-image, Gunicorn met Flask | Webinterface, openbare pagina, health endpoints | Nee, alleen via `nginx` |
| `api` | Hetzelfde applicatie-image, `DIENST=api` | API `/api/v1`, import van leden, health endpoints | Nee, alleen via de interne server van `nginx` |
| `worker` | Hetzelfde applicatie-image, ander startcommando | Heartbeat, dagelijkse opschoning | Nee |
| `integratie` | Eigen klein image uit `integratie/`, vervangbaar | Leden ophalen uit de bron en importeren via de API; terugschrijven voorbereid, uit | Nee; alleen uitgaand naar de bron |
| `db` | PostgreSQL 17 | Alle gegevens, ook foto's | Nee, alleen intern netwerk |

Er is één applicatie-image. `web`, `api` en `worker` verschillen alleen in startcommando, `DIENST` en databaserol. Zo gebruiken ze dezelfde domeinlaag en hetzelfde mutatielog. `integratie` is bewust een eigen image zonder applicatiecode, zodat een andere vereniging het kan vervangen.

Configuratie komt uit de omgeving (ADR-009). Logs gaan als JSON-regels naar stdout. Elke applicatiecontainer heeft een healthcheck in compose: `web` en `api` op `/health/live`, `db` met `pg_isready`, `worker` op een heartbeat in de database (ADR-010). Of `integratie` werkt, toont de statuspagina.

Databasemigraties draaien als een eenmalige stap bij het starten (`alembic upgrade head` in een init-container `migrate` van hetzelfde image, die `web`, `api` en `worker` afwachten). Zo draaien twee Gunicorn-workers nooit tegelijk een migratie.

## 3. Lagen en modulegrenzen

De applicatie heeft drie lagen. De regel is eenvoudig: alleen de domeinlaag wijzigt gegevens.

| Laag | Modules | Mag | Mag niet |
|------|---------|-----|----------|
| Ingang | `web` (blueprints met Jinja-templates), `api` (blueprint `/api/v1`, alleen in de dienst `api`), `taken` (worker), `cli` (beheercommando's) | Invoer lezen en valideren op vorm, rechten controleren, domeinfuncties aanroepen, uitvoer opmaken | Modellen direct wijzigen, bedrijfsregels herhalen |
| Domein | `domein/indeling`, `domein/boten`, `domein/toewijzing`, `domein/wachtlijst`, `domein/leden`, `domein/beheerders`, `domein/tokens`, `domein/instellingen`, `domein/log`, `domein/opschonen`, `domein/afbeeldingen` | Bedrijfsregels afdwingen, wijzigen binnen één transactie, het mutatielog schrijven | HTTP, sessies of templates kennen |
| Gegevens | `models` (SQLAlchemy 2) | Opslag | Bedrijfsregels bevatten |

Elke domeinfunctie die iets wijzigt, krijgt de handelende partij mee: een beheerder, een token of een taak. De functie controleert de regel, wijzigt, en schrijft de logregel in dezelfde transactie. Een wijziging zonder logregel kan daardoor niet bestaan. Een geweigerde wijziging levert een `Regelfout` met een vaste reden op. De webinterface toont die reden als melding; de API geeft dezelfde reden terug met status 409 of 422. Zo geldt BLB-034 vanzelf: er is geen tweede codepad.

De API leest, en schrijft alleen voor de import van leden door de integratiecontainer (intake, besluiten 2026-10-31; ADR-012). De leesfuncties in de domeinlaag bepalen ook welke velden zichtbaar zijn: zonder het recht persoonsgegevens geeft de domeinlaag geen adres, telefoonnummer en e-mailadres terug. De openbare pagina gebruikt een eigen leesfunctie die alleen plaatscode, bootnaam, foto en naam van de eigenaar oplevert. Wat niet wordt opgehaald, kan ook niet per ongeluk in een template of JSON-antwoord terechtkomen.

De applicatie praat met geen enkel extern systeem. De integratiecontainer haalt de leden uit de bron en stuurt ruwe records naar `PUT /api/v1/leden`; `domein/leden` valideert en slaat op (ADR-004, ADR-012).

Bewust weggelaten: een repository-laag boven SQLAlchemy, een servicecontainer of dependency-injectieframework, een eventbus en een aparte API-backend. Bij deze omvang lossen ze geen probleem op.

## 4. Datamodel op hoofdlijnen

Het datamodel heeft dertien tabellen. Namen volgen de begrippen van de backlog.

| Entiteit | Belangrijkste velden | Relaties en regels |
|----------|----------------------|--------------------|
| `rek` | naam, volgorde | Heeft plaatsen. Verwijderen kan alleen zonder toegewezen plaatsen. |
| `plaats` | code (uniek, te wijzigen), `publieke_sleutel` (uniek, vast), is_clubplaats, volgorde, `boot_id` (uniek, leeg als vrij) | Hoort bij één rek. Ten hoogste één boot (ADR-003). |
| `bootsoort` | naam | Startlijst van vijf soorten. Een tabel, geen vaste lijst in code, zodat BLB-028 later geen migratie vraagt. |
| `plaats_bootsoort` | plaats, bootsoort | Welke bootsoorten op een plaats passen. |
| `lid` | lidnummer (uniek), naam, adres, telefoon, e-mail, lid_sinds, opzegdatum, uit_bron_op | Alleen de import via de API wijzigt een lid (rol `botenloods_api`). Oud-lid is afgeleid: opzegdatum of uit_bron_op is gevuld en ligt in het verleden. |
| `boot` | naam, bootsoort, `lid_id` (leeg voor een clubboot), `afbeelding_id` | Een clubboot heeft geen lid. Een clubboot mag alleen op een clubplaats, een boot van een lid nooit. |
| `wachtlijst` | boot (uniek), aangemeld_op | De bootsoort volgt uit de boot, dus er is per bootsoort vanzelf een eigen lijst. |
| `afbeelding` | soort (foto), mime-type, inhoud (bytea), breedte, hoogte, `sleutel` (willekeurig, voor de URL) | ADR-008. |
| `beheerder` | naam, gebruikersnaam, actief, sessieversie, wachtwoordhash (leeg zonder wachtwoord), versleuteld TOTP-geheim, laatste TOTP-tijdstap, aantal mislukte pogingen, geblokkeerd_tot | Drie beheerders met gelijke rechten. Wachtwoord en TOTP gaan samen (ADR-001). |
| `passkey` | beheerder, credential-id, publieke sleutel, teller, naam, laatst_gebruikt | ADR-001. Een beheerder heeft nul of meer passkeys. |
| `uitnodiging` | beheerder, hash van de eenmalige code, verloopt_op, gebruikt_op | Voor het instellen van een inlogmethode en voor herstel van toegang. |
| `token` | naam, soort (persoonlijk of robot), beheerder (leeg bij robot), prefix, hash, rechten, ip_whitelist, verloopt_op, ingetrokken_op, laatst_gebruikt_op | ADR-005. |
| `logregel` | tijdstip, soort (mutatie of api), actor_soort, actor_id, actor_naam, actie, verwijzingen, gegevens (JSON) | ADR-006. Alleen toevoegen; de applicatie kent geen wijzigen of verwijderen behalve de opschoning. |

Daarnaast zijn er twee kleine technische tabellen: `instelling` (sleutel en waarde, voor naam en kleuren die de beheerder instelt, ADR-009) en `taakrun` (taak, start, einde, resultaat, aantallen, foutmelding, en de verzoeken om handmatig te starten, ADR-007).

De regels die de database zelf kan bewaken, staan als constraint in de database: unieke code, unieke publieke sleutel, een boot op hooguit één plaats (`plaats.boot_id` uniek), een boot hooguit één keer op de wachtlijst. De regels die gegevens uit meerdere tabellen vragen (clubplaats tegen clubboot, geschikte bootsoort, oud-lid), staan in `domein/toewijzing`. Die functie leest de plaats met `SELECT ... FOR UPDATE`, zodat twee beheerders niet tegelijk dezelfde plaats toewijzen. Plaats wijzigen (code, bootsoorten, clubplaats) en vrijgeven vergrendelen de plaats op dezelfde manier. Blokkeren, verwijderen en herstellen van een beheerder vergrendelen alle actieve accounts, en het intrekken van een eigen inlogmethode het eigen account; zo blijft er altijd een actieve beheerder met minstens één methode.

Verplaatsen van een boot is vrijgeven gevolgd door toewijzen, binnen één domeinfunctie en één transactie (aanname uit de backlog §8).

## 5. Repo-indeling

```
botenloods/
  app/
    __init__.py          create_app, blueprints registreren
    config.py            instellingen uit de omgeving
    models.py            alle tabellen
    domein/              bedrijfsregels, één module per onderwerp (§3)
    web/                 blueprints en templates per onderwerp
    web/static/          CSS met design tokens, kleine JS voor passkeys
    api/                 blueprint /api/v1 en openapi.yaml
    taken/               worker-lus, heartbeat, opschoning
    cli.py               beheerder uitnodigen, robottoken maken, seed
  integratie/            eigen image: bron (stub, later e-boekhouden), lus, aanroepen naar de API (ADR-012)
  migrations/            Alembic
  tests/
    unit/                domeinregels zonder HTTP
    integratie/          Flask-testclient tegen een echte PostgreSQL
    e2e/                 Playwright
    fixtures/            synthetische leden voor de stub
  docker/
    Dockerfile
    nginx/               publieke server en interne server op 8081
  huisstijl/             logo van de installatie, niet in git (ADR-008)
  secrets/               api_token van de integratiecontainer, niet in git (ADR-012)
  docker-compose.yml     productie-opbouw
  compose.dev.yml        aanvulling voor lokaal: poorten, herladen, testdatabase
  .env.example           alle variabelen, zonder geheimen
  pyproject.toml         afhankelijkheden met vaste versies, ruff, pytest
  docs/
    beheer/              beheerdocumentatie, onder meer integratiecontainer.md (ADR-012)
```

Eén `models.py` is genoeg voor vijftien tabellen. Splitsen kan later zonder gevolgen voor de lagen.

## 6. Ontwikkel- en testomgeving

### 6.1 Python en afhankelijkheden

De applicatie gebruikt Python 3.14 op het image `python:3.14-slim`. Heeft een afhankelijkheid op het moment van bouwen nog geen werkend wheel voor 3.14, dan wordt het 3.13; forge legt dat vast in `pyproject.toml`. Afhankelijkheden staan met vaste versies in een lockbestand (`uv lock`). De keuze van bibliotheken staat in ADR-011.

### 6.2 De stack lokaal starten

Lokaal start de ontwikkelaar de stack met:

1. `cp .env.example .env` en een eigen `SECRET_KEY` invullen. `compose.dev.yml` zet `LEDENBRON=stub` aan in `integratie` en koppelt een testlogo aan `web`.
2. `docker compose -f docker-compose.yml -f compose.dev.yml up --build`.
3. `docker compose exec api flask seed` voor de synthetische gegevens. Seed draait in `api`, omdat alleen die rol leden mag schrijven (ADR-012).
4. `docker compose exec web flask beheerder uitnodigen ontwikkelaar` geeft een eenmalige link; daarmee stelt de ontwikkelaar een passkey of een wachtwoord met TOTP in.
5. `docker compose exec web flask token robot integratie --recht leden:importeren --recht bootaantallen:lezen` geeft het token; dat komt in `secrets/api_token` (ADR-012).

Lokaal draait de applicatie op `http://localhost:8080`. Passkeys werken in browsers op `localhost` zonder TLS, dus lokaal is geen certificaat nodig. `compose.dev.yml` zet Flask in herlaadmodus en opent de databasepoort alleen op 127.0.0.1.

### 6.3 Seeddata

`flask seed` maakt een volledige, synthetische loods op de omvang van de vereniging, met een vaste random seed zodat elke run hetzelfde oplevert:

- 10 rekken met samen 160 plaatsen, waarvan 8 clubplaatsen en een mix van geschikte bootsoorten;
- 210 leden uit `tests/fixtures/leden.json`, via dezelfde domeinfunctie als de import, met 12 oud-leden, waarvan 4 nog een plaats hebben. De fixture bevat ook 2 oud-leden met een opzegdatum langer dan 5 jaar geleden; die slaat de import over (ADR-004). Een test voor de opschoning maakt zulke leden zelf aan;
- 180 boten, waarvan 6 clubboten, 150 met een plaats en 10 op de wachtlijst verdeeld over drie bootsoorten;
- een naam en kleuren voor een fictieve vereniging. Het testlogo komt niet uit seed maar uit `compose.dev.yml` (ADR-008).

Alle namen, adressen en nummers zijn verzonnen; e-mailadressen eindigen op `@example.org` (overlay §8). `flask seed` weigert te draaien als `APP_OMGEVING=productie`.

### 6.4 Testaccounts voor E2E

E2E-tests draaien met Playwright (Python) tegen de stack in compose. Inloggen met een passkey gebeurt met de virtuele authenticator van Chromium (WebAuthn via het Chrome DevTools Protocol), inloggen met een wachtwoord met `pyotp` en een testgeheim. Er komt dus geen inlogomweg in de applicatie.

| Account | Gebruik |
|---------|---------|
| `e2e-beheerder-1` | Standaardbeheerder voor alle happy flows, met passkey |
| `e2e-beheerder-wachtwoord` | Beheerder met wachtwoord en TOTP: inloggen, vergrendeling na vijf pogingen, herstel door een andere beheerder |
| `e2e-beheerder-2` | Tweede beheerder: tokens van een ander intrekken, laatste account niet blokkeren |
| `e2e-geblokkeerd` | Geblokkeerd account: inloggen moet mislukken |
| bezoeker | Geen account, voor de openbare pagina en de doorverwijzing naar het inlogscherm |

De testfixture roept `flask beheerder uitnodigen` aan, opent de link in Playwright en registreert een passkey bij de virtuele authenticator, of stelt een wachtwoord en TOTP in. Voor de API maakt de fixture een robottoken met de kleinste whitelist waarmee de test `api` bereikt; forge kiest die bij de bouw.

### 6.5 Tests

Unit- en integratietests draaien met pytest tegen een echte PostgreSQL in compose; er is geen SQLite-variant, omdat de applicatie PostgreSQL-typen (`cidr`, `bytea`, `jsonb`, arrays) gebruikt. Elke test draait in een transactie die na afloop wordt teruggedraaid. `tests/e2e/draai.sh` draait de E2E-tests per bestand met een pauze ertussen, zodat de rate limit van Nginx op inlogverzoeken (ADR-001) de suite niet blokkeert; met `-k` draait één selectie in één keer. De nepbron voor de tests van BLB-006 tot BLB-008 is een fixturebestand dat de test naar `PUT /api/v1/leden` stuurt. De integratiecontainer heeft eigen tests met de stub en een nep-API.

## 7. Componenten per slice

Slice 1 tot en met 3 volgen het voorstel in backlog §5. Voor de rest geldt §7.1.

| Slice | Stories | Geraakte componenten | ADR's |
|-------|---------|----------------------|-------|
| 1 | BLB-022, 001, 007, 006, 005, 010, 012, 020, 024, 025 | De vier containers van toen, `migrate`, models (rek, plaats, bootsoort, lid, boot, beheerder, passkey, uitnodiging, logregel, afbeelding), `domein/indeling`, `boten`, `toewijzing`, `leden`, `log`, `afbeeldingen`, `ledenbron` met stub, `taken` (alleen synchronisatie), `web` (inloggen, indeling, boten, plaatsdetail, openbare pagina), basistemplate met design tokens, `cli` | 001, 002, 003, 004, 006, 007, 008, 009, 011 |
| 2 | BLB-002, 003, 004, 008, 011, 023, 038, 036 | `domein/indeling` (`plaats_wijzigen`: bootsoorten, clubplaats en code in één functie met `FOR UPDATE`), `domein/toewijzing` (vrijgeven), `domein/leden` (oud-lid), `domein/beheerders` (beheerders beheren, eigen inlogmethodes), `web` (plaatsdetail, beheerders, profiel), health endpoints | 001, 003, 010 |
| 3 | BLB-015, 016, 019, 018, 017, 027 | `domein/indeling` (vrije plaatsen, plaatsen van oud-leden, Excel-export met openpyxl), `domein/leden` (zoeken, lid met boten), `domein/instellingen` (naam, kleuren, contrast, logo; rijen vergrendeld met `INSERT ... ON CONFLICT DO NOTHING` en `FOR UPDATE`), `web` (vrije plaatsen, opgezegd, lijst per lid, instellingen); de kleuren komen via de stylesheet `/huisstijl.css` in plaats van een `<style>`-blok met nonce (ADR-002, voorstel aan foundation) | 002, 008, 009, 011 |

Slice 1 is groot omdat de basis erin zit: containers, inloggen, mutatielog en de stub. Forge kan slice 1 intern splitsen in "stack, inloggen en log" en "indeling, boten en openbare pagina", zolang het log vanaf de eerste mutatie werkt.

### 7.1 Voorstel voor de volgende slices (2026-10-31)

De besluiten van 2026-10-31 halen de API naar voren: zonder API werkt de import van leden niet meer. Foundation stelt deze volgorde voor; apex past de backlog aan en kiest de nummers. Slice 1 tot en met 3 zijn af.

| Volgorde | Was | Inhoud | Geraakte componenten | ADR's |
|----------|-----|--------|----------------------|-------|
| A | nieuw | Logo uit de installatie en "(geschikt voor …)" in de Excel-export (issue #17) | `web` (logo uit `LOGO_BESTAND`, route `/logo/<hash>`), migratie die logo en route verwijdert, Nginx-locatie weg, `domein/indeling` (export) | 008, 009 |
| B | deel van 7 | API-basis: robottoken via de CLI, controle per aanroep, logging, rate limit, `GET /api/v1/ik` (deel van BLB-029, 031, 033, 034) | model `token`, `domein/tokens`, dienst `api` met rol `botenloods_api`, netwerken, interne Nginx-server op 8081, `openapi.yaml` | 005, 009, 011, 012 |
| C | nieuw | Integratiecontainer met stub; import, importverzoek en gemelde fout via de API; BLB-006, 007 en 008 opnieuw groen via de nieuwe route | `integratie/`, `domein/leden` (import), `taken` zonder synchronisatie, `app/ledenbron/` weg, seed in `api`, `docs/beheer/integratiecontainer.md` | 004, 007, 012 |
| D | 4 | BLB-013, 014 | model `wachtlijst`, `domein/wachtlijst`, koppeling met `domein/toewijzing` | 006 |
| E | 5 | BLB-021 | `web` (printpagina met kaartjes), QR-generatie | 003, 011 |
| F | 6 | BLB-026, 037, 009 | `domein/opschonen`, `taken` (opschoning), statuspagina, `GET /api/v1/bootaantallen`, `schrijf_bootaantallen` in de integratiecontainer (uit) | 004, 006, 007, 010, 012 |
| G | rest van 7 | Leesendpoints, persoonlijke tokens, tokenschermen, waarschuwing op de statuspagina (rest van BLB-029 tot en met 035) | `api`, `web` (tokenschermen) | 005, 010 |
| H | 8 | BLB-028 | `domein/indeling` (bootsoorten), `web` | geen nieuwe |

A staat los van de API en sluit issue #17. B gaat vóór C, omdat C het contract en het token uit B nodig heeft. C gaat vóór de wachtlijst, zodat BLB-008 (boten van oud-leden van de wachtlijst) meteen op de definitieve importroute wordt gebouwd. Wat G precies omvat, hangt af van open vraag 5 in §10.2.

## 8. Beveiliging

### 8.1 Dreigingen en maatregelen

| Dreiging | Ingang | Kans | Impact | Maatregel | ADR |
|----------|--------|------|--------|-----------|-----|
| Overname van een beheeraccount door phishing of een gelekt wachtwoord | Inlogscherm | M | H | Passkey: phishingbestendig. Wachtwoord met TOTP: argon2id, TOTP-code eenmalig bruikbaar, vergrendeling per account na vijf pogingen, rate limit per IP; phishing blijft mogelijk en is door de stakeholder geaccepteerd (restrisico) | 001 |
| Overgenomen open sessie voegt een eigen passkey toe, trekt een methode in, nodigt een beheerder uit of herstelt een collega | Profiel | L | H | Alleen binnen 10 minuten na de inlog; intrekken beëindigt alle sessies van de beheerder | 001 |
| Persoonsgegevens op de openbare pagina | `/p/<sleutel>` | M | H | Eigen leesfunctie met vier velden, E2E-test op het antwoord | 003 |
| Lijst van alle eigenaren ophalen door plaatsnummers op te tellen | `/p/<sleutel>` | M | M | Willekeurige publieke sleutel in plaats van een volgnummer | 003 |
| Gestolen of uitgelekt API-token | API | L | H | Hash in de database, IP-whitelist, korte geldigheid mogelijk, intrekken | 005 |
| Kwaadaardig bestand als foto of logo (XSS via SVG, verborgen locatiegegevens) | Upload van een foto; logobestand in de installatie | M | M | Alleen JPEG, PNG en WebP, opnieuw coderen met Pillow, EXIF verwijderen; een ongeldig logo wordt niet getoond | 008 |
| Formule in de Excel-export via een naam uit de ledenbron (bijvoorbeeld `=HYPERLINK(...)`) | Export | L | M | Tekst met `=` vooraan blijft tekst in het bestand; stuurtekens vallen weg | 011 |
| Ongeldige of gemanipuleerde gegevens uit de ledenbron, of een halve lijst van een vervangende container | `PUT /api/v1/leden` | L | M | Validatie per record in de domeinlaag, grens op grootte en aantal, afbreken bij een verdachte afname | 004, 012 |
| Overgenomen integratiecontainer of gelekt robottoken | API | L | H | Token met alleen `leden:importeren` en `bootaantallen:lezen`, whitelist `KOPPELNET`, geen toegang tot `db` of `api` buiten Nginx; het ergste gevolg is een import van gemanipuleerde leden, die de veiligheidsgrens en het log beperken | 005, 012 |
| API per ongeluk vanaf internet bereikbaar | Nginx | L | H | Publieke server kent geen route naar `api`; ontsluiten vraagt een apart compose-bestand; `api` zit op een intern netwerk | 012 |
| CSRF op beheeracties | Webinterface | M | M | CSRF-token op elk formulier, sessiecookie `SameSite=Lax`, `Secure`, `HttpOnly` | 011 |
| Inloggegevens van e-boekhouden in logs of statuspagina | Integratiecontainer, statuspagina | L | H | Alleen in de omgeving van `integratie`; de applicatie kent ze niet; een gemelde fout heeft een reden uit een vaste lijst | 004, 009, 012 |
| Vervalst IP-adres via `X-Forwarded-For` | API | M | H | Flask vertrouwt precies één proxy (Nginx); Nginx overschrijft de header | 005 |

### 8.2 Ontwerpprincipes

| Principe | Status | Toelichting |
|----------|--------|-------------|
| Minimale rechten | Compliant | Containers zonder root; database-accounts zonder superuser, per dienst een rol, alleen `api` schrijft leden; `integratie` zonder databasetoegang; tokens met losse rechten; persoonsgegevens alleen met apart recht |
| Gelaagde verdediging | Compliant | Nginx (rate limits, headers, CSP) voor Flask; constraints in de database onder de domeinregels |
| Veilig falen | Compliant | Import breekt af zonder wijziging; de API staat standaard aan maar alleen op het interne netwerk (`API_INGESCHAKELD=true`, whitelist `KOPPELNET`); terugschrijven staat uit; een ongeldig logo wordt niet getoond |
| Scheiding | Compliant | Eén plek voor regels; de enige externe koppeling zit in een eigen container die alleen de API kent |

### 8.3 Bekende restrisico's

Back-ups vallen buiten de applicatie. Een back-up bevat persoonsgegevens en foto's en ook gegevens die de opschoning al heeft verwijderd. Wie de installatie draait, moet de bewaartermijn van back-ups afstemmen op de termijn van 5 jaar. Dit staat als open vraag in §10.

## 9. Besluiten van de stakeholder

De stakeholder besloot over de eerste vijf keuzes op 2026-10-30 (bron: `docs/business/intake.md`, sectie "Besluiten op de architectuurvragen"). Besluit 1 en 5 wijken af van de aanbeveling van foundation en zijn in de ADR's herschreven. Besluit 6 en 7 zijn van 2026-10-31 (sectie "Besluiten van de stakeholder (2026-10-31)"); besluit 7 wijzigt de standaard van besluit 5.

| # | Besluit | Uitkomst (2026-10-30) | Gevolg |
|---|---------|-----------------------|--------|
| 1 | Inlogmethode voor beheerders (ADR-001) | Een beheerder logt in met een passkey of met een wachtwoord plus TOTP; beide zijn beschikbaar. Een eenmalige uitnodigingslink dient voor instellen en herstel. Afwijking van de aanbeveling (alleen passkeys). | De beheerder kiest bij de uitnodiging één of beide methodes. Wachtwoord met TOTP is te phishen; dat restrisico is geaccepteerd. Wie zijn toestel kwijt is, krijgt een herstellink van een andere beheerder. |
| 2 | Vaste domeinnaam en TLS per installatie | Besloten zoals aanbevolen: elke installatie heeft een eigen, blijvende (sub)domeinnaam met HTTPS. Nginx in de compose termineert TLS met een gemount certificaat; vernieuwen (bijvoorbeeld met certbot op de host) hoort bij de hosting. | Passkeys werken alleen op een vaste domeinnaam met HTTPS. De QR-codes op de kaartjes bevatten de domeinnaam: verandert die, dan moeten alle kaartjes opnieuw. |
| 3 | Wat "een boot in de loods" is voor de bewaartermijn | Besloten zoals aanbevolen: een oud-lid valt onder de opschoning zodra 5 jaar na de opzegdatum geen boot van het oud-lid nog een plaats heeft. Bij het opschonen worden ook de boten en foto's van het oud-lid verwijderd (ADR-006). | Een boot zonder plaats houdt het opschonen niet tegen. Wil de vereniging boten zonder plaats als "in de loods" tellen, dan blijven gegevens langer staan. |
| 4 | Begin van de termijn voor een lid dat uit de bron verdwijnt zonder opzegdatum | Besloten zoals aanbevolen: de datum waarop de synchronisatie het lid niet meer vond, telt als opzegdatum (ADR-004, ADR-006). | Zonder deze regel begint de termijn van zo'n oud-lid nooit en blijven de gegevens onbeperkt staan. |
| 5 | Wie de API aan- en uitzet (ADR-009) | De API gaat aan en uit in de installatie, via de omgevingsvariabele `API_INGESCHAKELD`, niet door de beheerder in de applicatie. Afwijking van de aanbeveling. De standaard is sinds besluit 7 `true`. | Er komt geen scherm voor de schakelaar. Wijzigen vraagt iemand met servertoegang en een herstart van `api`. |
| 6 | Waar het logo staat (ADR-008, ADR-009) | In de installatie (docker-compose), niet in de applicatie; wijzigen wordt niet gelogd. Naam en kleuren blijven in de applicatie. | Geen uploadscherm meer; het logo staat in `./huisstijl` en een nieuw logo vraagt een herstart van `web`. |
| 7 | Imports en exports (ADR-004, ADR-012) | Een aparte, vervangbare container doet alle imports en exports, alleen via de API over het interne netwerk. De API staat standaard aan met als whitelist het interne netwerk en is niet meer alleen-lezen. | Dienst `api` met eigen databaserol, interne Nginx-server, robottoken via de CLI; de synchronisatie verdwijnt uit de worker. |

## 10. Botsingen tussen bronnen en open vragen

### 10.1 Botsingen

De intake gaat voor. Deze botsingen zijn niet gladgestreken; apex hoort de backlog erop aan te passen.

| # | Botsing | Volgens de intake | Gevolg |
|---|---------|-------------------|--------|
| 1 | BLB-034 criterium 2 (een geweigerde wijziging via de API) en BLB-024 criterium 2 (een wijziging via een token) gaan uit van schrijven via de API. | Sinds 2026-10-31 schrijft de API alleen bij de import van leden. | Beide criteria zijn te testen met `PUT /api/v1/leden`: een import onder de veiligheidsgrens geeft 409, een geslaagde import een logregel met het token als actor. Apex past de criteria daarop aan. |
| 2 | Backlog §5 noemt de toegang tot de API van e-boekhouden niet bevestigd. | Er is toegang; voor nu komt er een stub. | Geen risico meer voor slice 1. |
| 3 | Overlay §4 en de repository noemen GitHub-issues; de algemene werkafspraken noemen Forgejo. | De intake noemt GitHub. | Geen architectuurgevolg; de regie bevestigt dit. |
| 4 | Intakestory 1 noemt "eventuele foto" bij de gegevens van de eigenaar; het domein kent alleen een foto van de boot. | Het domein in de intake: een boot heeft soms een foto. | Het ontwerp kent geen foto van een lid. |

### 10.2 Open vragen

| # | Vraag | Voor | Prioriteit | Blokkerend |
|---|-------|------|------------|------------|
| 1 | Wie maakt back-ups, en hoe lang worden die bewaard ten opzichte van de termijn van 5 jaar? | Stakeholder | Besloten | Besluit stakeholder 2026-10-30: back-ups vallen buiten de applicatie en volgen later bij de hosting |
| 2 | Welke API-velden levert e-boekhouden precies voor leden (adres als één veld of in delen, opzegdatum)? | Oracle of forge, bij de echte koppeling | L | Nee, de stub gebruikt het eigen formaat |
| 3 | Moet de openbare pagina ook via de plaatscode op te zoeken zijn ("code of link" in BLB-020)? Het ontwerp kent alleen de link. | Apex | Besloten | Besluit stakeholder 2026-10-30: alleen via de QR-link, geen zoeken op plaatscode |
| 4 | Botst het standaardsubnet `10.203.0.0/24` van `KOPPELNET` met een netwerk op de host van een vereniging? | Forge, bij de installatiebeschrijving | L | Nee, `KOPPELNET` is in te stellen |
| 5 | Persoonlijke tokens (BLB-029 en verder) zijn alleen nuttig als de API van buiten bereikbaar is, en de intake zegt dat de API niet vanaf internet bereikbaar is. Vervallen persoonlijke tokens en de leesendpoints voor buiten, of komt er een bewuste keuze per installatie (`compose.api-extern.yml`, ADR-012)? | Stakeholder | H | Ja, voor slice G (§7.1); niet voor A tot en met F |
| 6 | Mag een import ook leden met een `opzegdatum` in de toekomst aanmaken? Dat kan nu al via de stub; de vraag is of e-boekhouden dat levert. | Oracle of forge, bij de echte koppeling | L | Nee |

## 11. Proactieve bevindingen

| # | Bevinding | Categorie | Zekerheid | Actie | Prioriteit |
|---|-----------|-----------|-----------|-------|------------|
| 1 | Na het opschonen van een oud-lid kan de volgende synchronisatie het lid opnieuw aanmaken als e-boekhouden het nog levert. | Gegevensbescherming | Confirmed | De synchronisatie slaat records over waarvan de opzegdatum meer dan 5 jaar geleden ligt en die lokaal niet bestaan (ADR-004). | H |
| 2 | Een kapotte bron die een lege of halve lijst levert, maakt alle leden oud-lid. | Betrouwbaarheid | Probable | De synchronisatie breekt af als minder dan de helft van de actieve leden terugkomt (ADR-004). | H |
| 3 | Elke API-aanroep in het log geeft bij een robot die elke minuut vraagt ongeveer 2,6 miljoen regels in 5 jaar. De integratiecontainer doet precies dat met `GET /api/v1/leden/importverzoek`. | Schaal | Confirmed | Index op tijdstip en verwijzingen; prima voor PostgreSQL. Bij meer dan 10 miljoen regels per jaar aggregeren (ADR-006). | L |
| 5 | Het netwerk `achterkant` is `internal: true`; `web`, `api` en `worker` hebben dan geen uitgaand verkeer. | Betrouwbaarheid | Probable | Geen van de drie heeft dat nu nodig; forge controleert dat bij slice B. | L |
| 4 | De QR-codes op geprinte kaartjes hangen aan de domeinnaam. | Onderhoudbaarheid | Confirmed | Besluit 2 in §9. | M |

## 12. Wijzigingslog

| Versie | Datum | Wijziging |
|--------|-------|-----------|
| v0.1.0 | 2026-10-30 | Eerste versie met ADR-001 tot en met ADR-011 |
| v0.3.0 | 2026-10-31 | Besluiten stakeholder 2026-10-31: integratiecontainer en dienst `api` (ADR-012), API standaard aan op het interne netwerk, logo uit de installatie. §1 tot en met §11 bijgewerkt; voorstel voor de volgende slices in §7.1; ADR-004 v2.0.0, ADR-005, 007, 008, 009, 010 en 011 v1.1.0, ADR-002 v1.1.1 |
| v0.2.6 | 2026-10-31 | Slice 3 (issue #13): componenten in §7, stylesheet voor de kleuren in plaats van een nonce, dreiging formule-injectie in §8.1 |
| v0.2.5 | 2026-10-30 | Slice 2 (issue #11): BLB-038 in §7; `plaats_wijzigen` en de vergrendelingen in §4; E2E per bestand vanwege de rate limit (§6.5) |
| v0.2.4 | 2026-10-30 | ADR-001 v1.1.0 (backlog §7, vragen 9 en 10): methode toevoegen of intrekken vraagt een recente inlog, intrekken beëindigt alle sessies; dreiging toegevoegd in §8.1 |
| v0.2.3 | 2026-10-30 | Herstel slice 1b (issue #9): `flask seed` in de worker en `LEDENBRON` standaard leeg (§6.2); webrol alleen SELECT op `lid`; plaatscode uniek zonder onderscheid in hoofdletters |
| v0.2.2 | 2026-10-30 | Afwijkingen uit slice 1b: seed volgt ADR-004 (§6.3), `DIENST` (ADR-009), nieuwe poging na een fout (ADR-007) |
| v0.2.1 | 2026-10-30 | Afwijkingen uit slice 1a: Flask serveert de statische bestanden (§2); per dienst een eigen `DATABASE_URL` (ADR-009) |
| v0.2.0 | 2026-10-30 | Vijf besluiten van de stakeholder verwerkt. ADR-001 herschreven (passkey of wachtwoord met TOTP). ADR-009: API-schakelaar naar de omgeving, `TOTP_SLEUTEL` toegevoegd. ADR-011: argon2-cffi, pyotp, cryptography. ADR-004 en ADR-006: opschoonregels als besloten. §4, §6, §8 en §9 aangepast; ADR-status Aanvaard |
