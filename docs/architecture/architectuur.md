# Architectuur botenloodsbeheer

**Project:** botenloodsbeheer
**Versie:** v0.1.0
**Datum:** 2026-10-30
**Opgesteld door:** Foundation, Principal Architect
**Status:** Concept, wacht op de besluiten in §9
**Bronnen, in volgorde van gezag:** `docs/business/intake.md` (inclusief beide besluitensecties van 2026-10-30), `docs/PROJECT-OVERLAY.md`, `docs/product/backlog.md` v0.1.0.

## 1. Samenvatting

Botenloodsbeheer is één Flask-applicatie met één PostgreSQL-database, voor één vereniging per installatie. Het ontwerp is bewust klein: 160 plaatsen, 210 leden en 3 beheerders vragen geen services, wachtrij, cache of frontend-build. De webinterface is server-rendered. De externe API is een tweede ingang op dezelfde domeinlaag. Achtergrondwerk draait in een eigen container van hetzelfde image.

De drie keuzes met de meeste gevolgen zijn: beheerders loggen in met een passkey (ADR-001, besluit van de stakeholder nodig), een plaats heeft een vaste openbare sleutel los van de plaatscode zodat de QR-code blijft werken (ADR-003), en elke bedrijfsregel staat op één plek in de domeinlaag, die zowel de webinterface als de API gebruikt.

**Architectuurgezondheid:** Sound, met vijf open besluiten voor de stakeholder (§9).

## 2. Containers

De installatie bestaat uit vier containers in één `docker-compose.yml`. Ze draaien alle vier zonder root.

| Container | Inhoud | Taak | Bereikbaar van buiten |
|-----------|--------|------|-----------------------|
| `nginx` | Nginx (officieel image, unprivileged-variant) | TLS (zie §9, besluit 2), statische bestanden, beveiligingsheaders, rate limiting, maximale uploadgrootte, doorsturen naar `web` | Ja, poort 443 (en 80 voor doorverwijzing) |
| `web` | Applicatie-image, Gunicorn met Flask | Webinterface, openbare pagina, API `/api/v1`, health endpoints | Nee, alleen via `nginx` |
| `worker` | Hetzelfde applicatie-image, ander startcommando | Dagelijkse ledensynchronisatie, handmatig gestarte synchronisatie, dagelijkse opschoning | Nee |
| `db` | PostgreSQL 17 | Alle gegevens, ook foto's en logo | Nee, alleen intern netwerk |

Er is één applicatie-image. `web` en `worker` verschillen alleen in het startcommando. Zo bestaat er geen tweede codebasis voor achtergrondwerk en gebruikt de worker dezelfde domeinlaag en hetzelfde mutatielog.

Configuratie komt uit de omgeving (ADR-009). Logs gaan als JSON-regels naar stdout. Elke container heeft een healthcheck in compose: `web` op `/health/live`, `db` met `pg_isready`, `worker` op een heartbeat in de database (ADR-010).

Databasemigraties draaien als een eenmalige stap bij het starten (`alembic upgrade head` in een init-container `migrate` van hetzelfde image, die `web` en `worker` afwachten). Zo draaien twee Gunicorn-workers nooit tegelijk een migratie.

## 3. Lagen en modulegrenzen

De applicatie heeft drie lagen. De regel is eenvoudig: alleen de domeinlaag wijzigt gegevens.

| Laag | Modules | Mag | Mag niet |
|------|---------|-----|----------|
| Ingang | `web` (blueprints met Jinja-templates), `api` (blueprint `/api/v1`), `taken` (worker), `cli` (beheercommando's) | Invoer lezen en valideren op vorm, rechten controleren, domeinfuncties aanroepen, uitvoer opmaken | Modellen direct wijzigen, bedrijfsregels herhalen |
| Domein | `domein/indeling`, `domein/boten`, `domein/toewijzing`, `domein/wachtlijst`, `domein/leden`, `domein/beheerders`, `domein/tokens`, `domein/instellingen`, `domein/log`, `domein/opschonen`, `domein/afbeeldingen` | Bedrijfsregels afdwingen, wijzigen binnen één transactie, het mutatielog schrijven | HTTP, sessies of templates kennen |
| Gegevens | `models` (SQLAlchemy 2), `ledenbron` (interface met stub en later e-boekhouden) | Opslag en externe bron | Bedrijfsregels bevatten |

Elke domeinfunctie die iets wijzigt, krijgt de handelende partij mee: een beheerder, een token of een taak. De functie controleert de regel, wijzigt, en schrijft de logregel in dezelfde transactie. Een wijziging zonder logregel kan daardoor niet bestaan. Een geweigerde wijziging levert een `Regelfout` met een vaste reden op. De webinterface toont die reden als melding; de API geeft dezelfde reden terug met status 409 of 422. Zo geldt BLB-034 vanzelf: er is geen tweede codepad.

De API is in de eerste versie alleen-lezen (intake, besluit 2026-10-30). De leesfuncties in de domeinlaag bepalen ook welke velden zichtbaar zijn: zonder het recht persoonsgegevens geeft de domeinlaag geen adres, telefoonnummer en e-mailadres terug. De openbare pagina gebruikt een eigen leesfunctie die alleen plaatscode, bootnaam, foto en naam van de eigenaar oplevert. Wat niet wordt opgehaald, kan ook niet per ongeluk in een template of JSON-antwoord terechtkomen.

De ledenbron is de enige module die met een extern systeem praat. Ze levert ruwe records aan `domein/leden`, dat valideert en opslaat (ADR-004).

Bewust weggelaten: een repository-laag boven SQLAlchemy, een servicecontainer of dependency-injectieframework, een eventbus en een aparte API-backend. Bij deze omvang lossen ze geen probleem op.

## 4. Datamodel op hoofdlijnen

Het datamodel heeft dertien tabellen. Namen volgen de begrippen van de backlog.

| Entiteit | Belangrijkste velden | Relaties en regels |
|----------|----------------------|--------------------|
| `rek` | naam, volgorde | Heeft plaatsen. Verwijderen kan alleen zonder toegewezen plaatsen. |
| `plaats` | code (uniek, te wijzigen), `publieke_sleutel` (uniek, vast), is_clubplaats, volgorde, `boot_id` (uniek, leeg als vrij) | Hoort bij één rek. Ten hoogste één boot (ADR-003). |
| `bootsoort` | naam | Startlijst van vijf soorten. Een tabel, geen vaste lijst in code, zodat BLB-028 later geen migratie vraagt. |
| `plaats_bootsoort` | plaats, bootsoort | Welke bootsoorten op een plaats passen. |
| `lid` | lidnummer (uniek), naam, adres, telefoon, e-mail, lid_sinds, opzegdatum, uit_bron_op | Alleen de synchronisatie wijzigt een lid. Oud-lid is afgeleid: opzegdatum of uit_bron_op is gevuld en ligt in het verleden. |
| `boot` | naam, bootsoort, `lid_id` (leeg voor een clubboot), `afbeelding_id` | Een clubboot heeft geen lid. Een clubboot mag alleen op een clubplaats, een boot van een lid nooit. |
| `wachtlijst` | boot (uniek), aangemeld_op | De bootsoort volgt uit de boot, dus er is per bootsoort vanzelf een eigen lijst. |
| `afbeelding` | soort (foto of logo), mime-type, inhoud (bytea), breedte, hoogte, `sleutel` (willekeurig, voor de URL) | ADR-008. |
| `beheerder` | naam, gebruikersnaam, actief, sessieversie | Drie beheerders met gelijke rechten. |
| `passkey` | beheerder, credential-id, publieke sleutel, teller, naam, laatst_gebruikt | ADR-001. |
| `uitnodiging` | beheerder, hash van de eenmalige code, verloopt_op, gebruikt_op | Voor het registreren van een passkey en voor herstel van toegang. |
| `token` | naam, soort (persoonlijk of robot), beheerder (leeg bij robot), prefix, hash, rechten, ip_whitelist, verloopt_op, ingetrokken_op, laatst_gebruikt_op | ADR-005. |
| `logregel` | tijdstip, soort (mutatie of api), actor_soort, actor_id, actor_naam, actie, verwijzingen, gegevens (JSON) | ADR-006. Alleen toevoegen; de applicatie kent geen wijzigen of verwijderen behalve de opschoning. |

Daarnaast zijn er twee kleine technische tabellen: `instelling` (sleutel en waarde, voor wat de beheerder instelt, ADR-009) en `taakrun` (taak, start, einde, resultaat, aantallen, foutmelding, en de verzoeken om handmatig te starten, ADR-007).

De regels die de database zelf kan bewaken, staan als constraint in de database: unieke code, unieke publieke sleutel, een boot op hooguit één plaats (`plaats.boot_id` uniek), een boot hooguit één keer op de wachtlijst. De regels die gegevens uit meerdere tabellen vragen (clubplaats tegen clubboot, geschikte bootsoort, oud-lid), staan in `domein/toewijzing`. Die functie leest de plaats met `SELECT ... FOR UPDATE`, zodat twee beheerders niet tegelijk dezelfde plaats toewijzen.

Verplaatsen van een boot is vrijgeven gevolgd door toewijzen, binnen één domeinfunctie en één transactie (aanname uit de backlog §8).

## 5. Repo-indeling

```
botenloods/
  app/
    __init__.py          create_app, blueprints registreren
    config.py            instellingen uit de omgeving
    models.py            alle tabellen
    domein/              bedrijfsregels, één module per onderwerp (§3)
    ledenbron/           interface, stub, later e-boekhouden
    web/                 blueprints en templates per onderwerp
    web/static/          CSS met design tokens, kleine JS voor passkeys
    api/                 blueprint /api/v1 en openapi.yaml
    taken/               worker-lus, synchronisatie, opschoning
    cli.py               beheerder uitnodigen, seed, taak starten
  migrations/            Alembic
  tests/
    unit/                domeinregels zonder HTTP
    integratie/          Flask-testclient tegen een echte PostgreSQL
    e2e/                 Playwright
    fixtures/            synthetische leden voor de stub
  docker/
    Dockerfile
    nginx.conf
  docker-compose.yml     productie-opbouw
  compose.dev.yml        aanvulling voor lokaal: poorten, herladen, testdatabase
  .env.example           alle variabelen, zonder geheimen
  pyproject.toml         afhankelijkheden met vaste versies, ruff, pytest
  docs/
```

Eén `models.py` is genoeg voor vijftien tabellen. Splitsen kan later zonder gevolgen voor de lagen.

## 6. Ontwikkel- en testomgeving

### 6.1 Python en afhankelijkheden

De applicatie gebruikt Python 3.14 op het image `python:3.14-slim`. Heeft een afhankelijkheid op het moment van bouwen nog geen werkend wheel voor 3.14, dan wordt het 3.13; forge legt dat vast in `pyproject.toml`. Afhankelijkheden staan met vaste versies in een lockbestand (`uv lock`). De keuze van bibliotheken staat in ADR-011.

### 6.2 De stack lokaal starten

Lokaal start de ontwikkelaar de stack met:

1. `cp .env.example .env` en een eigen `SECRET_KEY` invullen. `LEDENBRON=stub` staat standaard aan.
2. `docker compose -f docker-compose.yml -f compose.dev.yml up --build`.
3. `docker compose exec web flask seed` voor de synthetische gegevens.
4. `docker compose exec web flask beheerder uitnodigen ontwikkelaar` geeft een eenmalige link; daarmee registreert de ontwikkelaar een passkey.

Lokaal draait de applicatie op `http://localhost:8080`. Passkeys werken in browsers op `localhost` zonder TLS, dus lokaal is geen certificaat nodig. `compose.dev.yml` zet Flask in herlaadmodus en opent de databasepoort alleen op 127.0.0.1.

### 6.3 Seeddata

`flask seed` maakt een volledige, synthetische loods op de omvang van de vereniging, met een vaste random seed zodat elke run hetzelfde oplevert:

- 10 rekken met samen 160 plaatsen, waarvan 8 clubplaatsen en een mix van geschikte bootsoorten;
- 210 leden via de stub-ledenbron uit `tests/fixtures/leden.json`, met 12 oud-leden, waarvan 4 nog een plaats hebben en 2 met een opzegdatum langer dan 5 jaar geleden (voor de opschoning);
- 180 boten, waarvan 6 clubboten, 150 met een plaats en 10 op de wachtlijst verdeeld over drie bootsoorten;
- een naam en kleuren voor een fictieve vereniging en een testlogo.

Alle namen, adressen en nummers zijn verzonnen; e-mailadressen eindigen op `@example.org` (overlay §8). `flask seed` weigert te draaien als `APP_OMGEVING=productie`.

### 6.4 Testaccounts voor E2E

E2E-tests draaien met Playwright (Python) tegen de stack in compose. Inloggen met een passkey gebeurt met de virtuele authenticator van Chromium (WebAuthn via het Chrome DevTools Protocol). Er komt dus geen inlogomweg in de applicatie.

| Account | Gebruik |
|---------|---------|
| `e2e-beheerder-1` | Standaardbeheerder voor alle happy flows |
| `e2e-beheerder-2` | Tweede beheerder: tokens van een ander intrekken, laatste account niet blokkeren |
| `e2e-geblokkeerd` | Geblokkeerd account: inloggen moet mislukken |
| bezoeker | Geen account, voor de openbare pagina en de doorverwijzing naar het inlogscherm |

De testfixture roept `flask beheerder uitnodigen` aan, opent de link in Playwright en registreert een passkey bij de virtuele authenticator. Voor de API maakt de fixture een robottoken met whitelist `127.0.0.1/32` en `::1/128`.

### 6.5 Tests

Unit- en integratietests draaien met pytest tegen een echte PostgreSQL in compose; er is geen SQLite-variant, omdat de applicatie PostgreSQL-typen (`cidr`, `bytea`, `jsonb`, arrays) gebruikt. Elke test draait in een transactie die na afloop wordt teruggedraaid. De stub-ledenbron is ook de nepbron voor de tests van BLB-006 tot BLB-008: een test zet een ander fixturebestand neer en draait de synchronisatie.

## 7. Componenten per slice

De slices volgen het voorstel in backlog §5.

| Slice | Stories | Geraakte componenten | ADR's |
|-------|---------|----------------------|-------|
| 1 | BLB-022, 001, 007, 006, 005, 010, 012, 020, 024, 025 | Alle vier containers, `migrate`, models (rek, plaats, bootsoort, lid, boot, beheerder, passkey, uitnodiging, logregel, afbeelding), `domein/indeling`, `boten`, `toewijzing`, `leden`, `log`, `afbeeldingen`, `ledenbron` met stub, `taken` (alleen synchronisatie), `web` (inloggen, indeling, boten, plaatsdetail, openbare pagina), basistemplate met design tokens, `cli` | 001, 002, 003, 004, 006, 007, 008, 009, 011 |
| 2 | BLB-002, 003, 004, 008, 011, 023, 036 | `domein/indeling` (bootsoorten per plaats, clubplaats, code wijzigen), `domein/toewijzing` (vrijgeven), `domein/leden` (oud-lid), `domein/beheerders`, `web` (beheerders), health endpoints | 001, 003, 010 |
| 3 | BLB-015, 016, 019, 018, 017, 027 | `web` (overzichten, lijst per lid, zoeken), Excel-export, `domein/instellingen`, logo-upload, design tokens uit instellingen | 008, 009, 011 |
| 4 | BLB-013, 014 | model `wachtlijst`, `domein/wachtlijst`, koppeling met `domein/toewijzing` | 006 |
| 5 | BLB-021 | `web` (printpagina met kaartjes), QR-generatie | 003, 011 |
| 6 | BLB-026, 037, 009 | `domein/opschonen`, `taken` (opschoning), statuspagina, terugschrijven in de ledenbron (uit) | 004, 006, 007, 010 |
| 7 | BLB-029 tot en met 035 | model `token`, `domein/tokens`, `api` met OpenAPI, Nginx rate limiting, tokenschermen, waarschuwing op de statuspagina | 005, 009, 010 |
| 8 | BLB-028 | `domein/indeling` (bootsoorten), `web` | geen nieuwe |

Slice 1 is groot omdat de basis erin zit: containers, inloggen, mutatielog en de stub. Forge kan slice 1 intern splitsen in "stack, inloggen en log" en "indeling, boten en openbare pagina", zolang het log vanaf de eerste mutatie werkt.

## 8. Beveiliging

### 8.1 Dreigingen en maatregelen

| Dreiging | Ingang | Kans | Impact | Maatregel | ADR |
|----------|--------|------|--------|-----------|-----|
| Overname van een beheeraccount door phishing of een gelekt wachtwoord | Inlogscherm | M | H | Passkeys: phishingbestendig, geen wachtwoord om te lekken | 001 |
| Persoonsgegevens op de openbare pagina | `/p/<sleutel>` | M | H | Eigen leesfunctie met vier velden, E2E-test op het antwoord | 003 |
| Lijst van alle eigenaren ophalen door plaatsnummers op te tellen | `/p/<sleutel>` | M | M | Willekeurige publieke sleutel in plaats van een volgnummer | 003 |
| Gestolen of uitgelekt API-token | API | L | H | Hash in de database, IP-whitelist, korte geldigheid mogelijk, intrekken | 005 |
| Kwaadaardig bestand als foto of logo (XSS via SVG, verborgen locatiegegevens) | Upload | M | M | Alleen JPEG, PNG en WebP, opnieuw coderen met Pillow, EXIF verwijderen | 008 |
| Ongeldige of gemanipuleerde gegevens uit de ledenbron | Worker | L | M | Validatie per record, afbreken bij een verdachte afname | 004 |
| CSRF op beheeracties | Webinterface | M | M | CSRF-token op elk formulier, sessiecookie `SameSite=Lax`, `Secure`, `HttpOnly` | 011 |
| Inloggegevens van e-boekhouden in logs of statuspagina | Worker, statuspagina | L | H | Alleen in de omgeving, nooit in foutmeldingen die worden opgeslagen | 004, 009 |
| Vervalst IP-adres via `X-Forwarded-For` | API | M | H | Flask vertrouwt precies één proxy (Nginx); Nginx overschrijft de header | 005 |

### 8.2 Ontwerpprincipes

| Principe | Status | Toelichting |
|----------|--------|-------------|
| Minimale rechten | Compliant | Containers zonder root; database-account zonder superuser; tokens met losse rechten; persoonsgegevens alleen met apart recht |
| Gelaagde verdediging | Compliant | Nginx (rate limits, headers, CSP) voor Flask; constraints in de database onder de domeinregels |
| Veilig falen | Compliant | Synchronisatie breekt af zonder wijziging; API staat standaard uit; terugschrijven staat uit |
| Scheiding | Compliant | Eén plek voor regels; ledenbron als enige externe koppeling |

### 8.3 Bekende restrisico's

Back-ups vallen buiten de applicatie. Een back-up bevat persoonsgegevens en foto's en ook gegevens die de opschoning al heeft verwijderd. Wie de installatie draait, moet de bewaartermijn van back-ups afstemmen op de termijn van 5 jaar. Dit staat als open vraag in §10.

## 9. Besluiten voor de stakeholder

Deze vijf keuzes vragen iets van de beheerders of van de vereniging. Foundation geeft een aanbeveling en kiest niet definitief.

| # | Besluit | Aanbeveling | Gevolg van de aanbeveling |
|---|---------|-------------|---------------------------|
| 1 | Inlogmethode voor beheerders (ADR-001) | Alleen passkeys, met een eenmalige uitnodigingslink voor registratie en herstel. Geen wachtwoord, geen TOTP. | Elke beheerder heeft een telefoon of computer met passkey-ondersteuning (vrijwel elk toestel sinds 2023) of een hardwaresleutel. Wie zijn toestel kwijt is, krijgt een nieuwe link van een andere beheerder. |
| 2 | Vaste domeinnaam en TLS per installatie | Elke installatie krijgt een eigen, blijvende (sub)domeinnaam met HTTPS. Nginx in de compose termineert TLS met een gemount certificaat; vernieuwen (bijvoorbeeld met certbot op de host) hoort bij de hosting. | Passkeys werken alleen op een vaste domeinnaam met HTTPS. De QR-codes op de kaartjes bevatten de domeinnaam: verandert die, dan moeten alle kaartjes opnieuw. |
| 3 | Wat "een boot in de loods" is voor de bewaartermijn | Een oud-lid valt onder de opschoning zodra 5 jaar na de opzegdatum geen boot van het oud-lid nog een plaats heeft. Bij het opschonen worden ook de boten en foto's van het oud-lid verwijderd. | Een boot zonder plaats houdt het opschonen niet tegen. Wil de vereniging boten zonder plaats als "in de loods" tellen, dan blijven gegevens langer staan. |
| 4 | Begin van de termijn voor een lid dat uit de bron verdwijnt zonder opzegdatum | De datum waarop de synchronisatie het lid niet meer vond, telt als opzegdatum. | Zonder deze regel begint de termijn van zo'n oud-lid nooit en blijven de gegevens onbeperkt staan. |
| 5 | Wie de API aan- en uitzet (ADR-009) | De beheerder in de applicatie, standaard uit, met een logregel. | Er is geen systeembeheerrol (intake). Een schakelaar in de omgeving zou iemand met servertoegang vragen voor een gewone beheerkeuze. |

## 10. Botsingen tussen bronnen en open vragen

### 10.1 Botsingen

De intake gaat voor. Deze botsingen zijn niet gladgestreken; apex hoort de backlog erop aan te passen.

| # | Botsing | Volgens de intake | Gevolg |
|---|---------|-------------------|--------|
| 1 | BLB-034 criterium 2 (een geweigerde wijziging via de API) en BLB-024 criterium 2 (een wijziging via een token) gaan uit van schrijven via de API. | De API is in de eerste versie alleen-lezen. | Deze criteria zijn in versie 1 niet te testen. De architectuur maakt ze later mogelijk zonder tweede codepad (§3). |
| 2 | Backlog §5 noemt de toegang tot de API van e-boekhouden niet bevestigd. | Er is toegang; voor nu komt er een stub. | Geen risico meer voor slice 1. |
| 3 | Overlay §4 en de repository noemen GitHub-issues; de algemene werkafspraken noemen Forgejo. | De intake noemt GitHub. | Geen architectuurgevolg; de regie bevestigt dit. |
| 4 | Intakestory 1 noemt "eventuele foto" bij de gegevens van de eigenaar; het domein kent alleen een foto van de boot. | Het domein in de intake: een boot heeft soms een foto. | Het ontwerp kent geen foto van een lid. |

### 10.2 Open vragen

| # | Vraag | Voor | Prioriteit | Blokkerend |
|---|-------|------|------------|------------|
| 1 | Wie maakt back-ups, en hoe lang worden die bewaard ten opzichte van de termijn van 5 jaar? | Stakeholder | Besloten | Besluit stakeholder 2026-10-30: back-ups vallen buiten de applicatie en volgen later bij de hosting |
| 2 | Welke API-velden levert e-boekhouden precies voor leden (adres als één veld of in delen, opzegdatum)? | Oracle of forge, bij de echte koppeling | L | Nee, de stub gebruikt het eigen formaat |
| 3 | Moet de openbare pagina ook via de plaatscode op te zoeken zijn ("code of link" in BLB-020)? Het ontwerp kent alleen de link. | Apex | Besloten | Besluit stakeholder 2026-10-30: alleen via de QR-link, geen zoeken op plaatscode |

## 11. Proactieve bevindingen

| # | Bevinding | Categorie | Zekerheid | Actie | Prioriteit |
|---|-----------|-----------|-----------|-------|------------|
| 1 | Na het opschonen van een oud-lid kan de volgende synchronisatie het lid opnieuw aanmaken als e-boekhouden het nog levert. | Gegevensbescherming | Confirmed | De synchronisatie slaat records over waarvan de opzegdatum meer dan 5 jaar geleden ligt en die lokaal niet bestaan (ADR-004). | H |
| 2 | Een kapotte bron die een lege of halve lijst levert, maakt alle leden oud-lid. | Betrouwbaarheid | Probable | De synchronisatie breekt af als minder dan de helft van de actieve leden terugkomt (ADR-004). | H |
| 3 | Elke API-aanroep in het log geeft bij een robot die elke minuut vraagt ongeveer 2,6 miljoen regels in 5 jaar. | Schaal | Probable | Index op tijdstip en verwijzingen; prima voor PostgreSQL. Bij meer dan 10 miljoen regels per jaar aggregeren (ADR-006). | L |
| 4 | De QR-codes op geprinte kaartjes hangen aan de domeinnaam. | Onderhoudbaarheid | Confirmed | Besluit 2 in §9. | M |

## 12. Wijzigingslog

| Versie | Datum | Wijziging |
|--------|-------|-----------|
| v0.1.0 | 2026-10-30 | Eerste versie met ADR-001 tot en met ADR-011 |
