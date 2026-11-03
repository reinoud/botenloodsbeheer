# Projectoverlay botenloodsbeheer

**Project:** botenloodsbeheer
**Geldt voor:** alle agents in dit project
**Versie overlay:** v0.3.17
**Beheer:** regie (hoofdsessie), na akkoord van de stakeholder
**Status:** concept
**Bijgewerkt:** 2026-11-03

Sjabloon: `/Users/reinoud/Projects/AI/Prompt Pack/00c. Project Overlay Template - v1.14.0.md`.

## 1. Doel

Deze overlay legt de regels vast die alleen voor botenloodsbeheer gelden. Hij vult de generieke agentprompts en de governance in `/Users/reinoud/Projects/AI/Prompt Pack/` aan en vervangt ze niet.

## 2. Reikwijdte

De overlay geldt voor elk werk in de repository `/Users/reinoud/git/botenloods` (GitHub: `reinoud/botenloodsbeheer`). Hij geldt niet voor andere projecten.

## 3. Projectcontext

Bronnen: `docs/business/intake.md` (leidend, inclusief de besluiten van 2026-10-30) en `docs/business/business-outline.md`.

| Onderdeel | Beschrijving |
|-----------|--------------|
| Aanleiding en probleem | De kanovereniging houdt de indeling van de botenloods bij in een spreadsheet. Daarin is niet goed te zien welke boot op welke plaats hoort, van wie die is, welke plaatsen vrij zijn en wie op de wachtlijst staat. |
| Product | Webapplicatie voor het beheer van stallingsplaatsen in de botenloods, met wachtlijst per bootsoort, overzichten, Excel-export, printbare kaartjes met QR-code en een openbare pagina per plaats. |
| Gebruikers | 3 beheerders met dezelfde rechten. Bezoekers en leden zonder account zien alleen de openbare pagina. API-gebruikers met een persoonlijk token of een robottoken. |
| Omvang | Ongeveer 10 rekken, 160 plaatsen, 210 leden en 180 boten. |
| Stack | Python, Flask, Gunicorn en PostgreSQL, in docker-compose, achter Traefik (ADR-013). |
| Gevoeligheid van gegevens | Persoonsgegevens van leden en oud-leden (naam, adres, telefoon, e-mail, lidmaatschapsdata). Openbaar alleen de naam van de eigenaar en de foto van de boot, met instemming van de leden. |
| Bron van leden | e-boekhouden, via een aparte en vervangbare integratiecontainer die alleen via de API werkt (ADR-012). Leden worden niet in de applicatie beheerd. |
| Uitrol | Eigen docker-compose per vereniging. |
| Stand | Slice 1 tot en met 10 gebouwd. Traefik vervangt Nginx (#29). Gebruikers- en beheerdocumentatie in `documentatie/` (#30). |

## 4. Werkwijze

- Volgorde: apex (backlog en user stories), foundation (architectuur en ADR's), forge (delivery in slices).
- Open werk staat in GitHub-issues van `reinoud/botenloodsbeheer`, met dezelfde regels als de Forgejo-afspraak in `~/.claude/CLAUDE.md`: type en label, sluiten met commit, test en bewijs.
- Review vóór elke codecommit volgens `~/.claude/CLAUDE.md`. Voor inloggen, tokens, autorisatie en de koppeling met e-boekhouden reviewt aegis mee.
- Elk agent dat code schrijft of reviewt, gebruikt de skill `ponytail`.
- Teksten volgen de skill `schrijfstijl`.
- Normenbibliotheek: `/Users/reinoud/Projects/AI/01. Standaarden/`. Raadplegen mag, kopiëren niet.

### Briefingchecklist

De regie loopt deze lijst na bij elke agentopdracht.

- Geef de omvang (10 rekken, 160 plaatsen, 210 leden, 180 boten) en de rollen (3 gelijke beheerders, geen systeembeheerrol) mee.
- `docs/business/intake.md` is leidend boven de business outline en boven eigen inschatting.
- Geef bij een omvang het woordbudget per onderdeel, niet alleen een totaal.
- Zeg welke open vragen blokkerend zijn, of laat het agent dat expliciet per vraag markeren.
- Of een instelling in de applicatie (door de beheerder) of in de installatie (omgeving) staat, beslist foundation per instelling in een ADR.
- Laat apex elk acceptatiecriterium toetsen aan de besluiten in de intake; een criterium dat een besluit tegenspreekt, gaat terug als vraag.
- Laat foundation bij een besluit dat een ontwerpdetail openlaat de veiligste eenvoudige variant kiezen en die melden. Nieuwe omgevingsvariabelen en afhankelijkheden die een besluit nodig maakt, mag foundation toevoegen en moet hij melden.
- Controleer vóór een bouwopdracht of Docker draait, en noem in de opdracht welke images al lokaal staan.
- Een afwijking van een ADR die alleen namen of de plaats van een instelling raakt (zoals een omgevingsvariabele per dienst), mag het bouwende agent doorvoeren en melden. Foundation werkt de ADR daarna bij.
- Elke E2E-test draait ook los. Laat de reviewer één test met `-k` draaien als controle op de volgorde.
- Geef een reviewer de paden van de ADR's en de verwachte waarden voor drempels (rate limit, vergrendeling, sessieduur), zodat hij toetst tegen een norm.
- Noem bij een seed of fixture welke regel voorgaat als architectuur §6.3 botst met een ADR (standaard: de ADR).
- Geef bij een geplande taak aan hoe vaak die na een fout opnieuw mag proberen.
- Vraagt een domeinfunctie om `FOR UPDATE`, lever dan een test met twee sessies die de race laat zien, of noteer in het issue waarom die test ontbreekt.
- Losse controles in Python draaien met `docker compose exec -T web python -c ...`, niet in de lokale `.venv`.
- Wijzig je databaserechten, zoek dan eerst welke tests en seedcode als die rol schrijven, en noem in je antwoord welke tests je hebt aangepast.
- Tekstwijzigingen in bestanden met python3, niet met sed (de sed-variant verschilt per omgeving).
- Migratiecontroles: downgrade en upgrade via `docker compose -f docker-compose.yml -f compose.dev.yml run --rm migrate alembic ...`; databasecontroles in de db-container met `psql -U botenloods -d botenloods`. Controleer na een migratie de rechten in de database.
- Laat bij elke bewaartermijn nalopen wat er met kopieën gebeurt: logs, back-ups, een externe bron die opnieuw synchroniseert, en verwijzingen in andere tabellen.
- Haal een issue op met `gh issue view <nr> -R reinoud/botenloodsbeheer --json title,body,comments`; `--comments` alleen toont de tekst van het issue niet.
- De backlog heeft geen wijzigingslog; de versie gaat omhoog zonder logregel.
- Heeft een document nog geen versie of wijzigingslog, begin dan op v1.0.0 en voeg onderaan een wijzigingslog toe.
- Na een besluit van foundation: voeg voor elk besluit een acceptatiecriterium toe aan de story, of meld waarom niet.
- De rate limit op `/inloggen` en `/uitnodiging` telt alle E2E-tests samen; `tests/e2e/draai.sh` draait per bestand met 40 seconden pauze. Houd een nieuw E2E-bestand onder 20 inlogverzoeken.
- Een logveld met de naam `code`, `adres`, `telefoon` of `email` staat in het log als `gewijzigd`; kies een andere sleutel als de waarde zichtbaar moet zijn.
- Noem bij elk verschoven criterium ook de criteria die van dezelfde latere story afhangen.
- Komt een handeling die eerst alleen via de CLI kon in de webinterface, noem dat in de brief aan de reviewer. Elke webroute met blijvend effect (een link, een nieuw account, een nieuwe inlogmethode) vraagt een recente inlog (ADR-001).
- Een racetest voor een domeinfunctie laadt het object eerst in dezelfde sessie, zoals `laad_beheerder` dat doet, zodat verouderde attributen na `with_for_update` zichtbaar worden. Gebruik `populate_existing=True` bij een vergrendeling van een object dat al geladen kan zijn.
- Een E2E-test die gedeelde instellingen wijzigt, zet ze ook terug als hij faalt (try/finally), of krijgt een eigen installatie.
- Geef een nieuwe webmodule geen naam die al bestaat in `app.web` (zoals een domeinmodule of functie); controleer na het toevoegen dat de route bestaat met `flask routes` of een unittest.
- Noem bij een grenstest beide kanten van de grens met de testnaam die elke kant dekt.
- Draai een mutant tegen het hele testbestand van de wijziging, niet met een `-k`-selectie op naam.
- Een racetest moet falen met een mutant zonder de vergrendeling. Overleeft de mutant, meld dan waarom de vergrendeling toch nodig is.
- Draai de volledige unitsuite vlak vóór de oplevering opnieuw en meld ook errors (niet alleen failures). Een test die los slaagt maar in de suite een error geeft, telt niet als geslaagd.
- Komt er een nieuwe route met querystring of padparameter die persoonsgegevens kan bevatten, controleer dan het maskeren in de toegangslog van Gunicorn (`app/toegangslog.py`).
- Meldt een agent dat een mutant overleeft, dan noemt hij de exacte diff van die mutant en het commando, zodat de reviewer hetzelfde kan draaien.
- Een test met `filterwarnings("error")` noemt de categorie van de waarschuwing, zodat waarschuwingen uit andere tests hem niet laten falen.
- Raakt een besluit van de stakeholder ook de overlay, dan noemt foundation de verouderde regels in de overlay; de regie werkt ze bij.
- Tel een nieuw ADR met `wc -w` vóór de oplevering en houd 10 procent marge onder het budget.
- Draai vóór de oplevering `git diff` op de leidende bronnen; een besluit dat tijdens het werk is bijgekomen, gaat voor de opdracht. Meld het in je antwoord.
- Na een wijziging of `up --build` die `web`, `api` of `integratie` opnieuw aanmaakt, wacht je tot de containers healthy zijn voordat je E2E-tests of curl-controles draait; tot dan geeft Traefik 404. Een herstart van de proxy is niet nodig.
- Een test op een grens (grootte, aantal, duur) gebruikt invoer die zonder die grens geldig is, en de mutant zonder de grens moet falen.
- ADR-008 "zonder metadata" betekent zonder EXIF, tekstblokken en ICC-profiel; de test en de reviewer gebruiken een bronbestand met alle drie.
- Een geparametriseerde test met binaire of grote invoer krijgt `ids=`.
- Een los controlescript in de testcontainer draai je met `-e PYTHONPATH=/app` en een volume uit de scratchpad.
- Een reviewer die een downgrade draait, doet dat op een eigen database (`nieuwe_database`), of meldt vooraf aan de andere reviewers dat de gedeelde database even op de vorige revisie staat.
- Draai geen compose-commando terwijl een `git stash` actief is; vergelijk een baseline in een aparte worktree.
- Controleer na elke wijziging aan de proxy of de toegangslog dat elk verzoek precies één logregel geeft, in het formaat `zonder_code`, in de log van `web` of `api`, en niets in de log van Traefik.
- Elke nieuwe omgevingsvariabele krijgt een test die de variabele zet en `create_app` aanroept (geldige en ongeldige waarde); een test die alleen `app.config` overschrijft, telt niet.
- Wijkt de bouwer af van een ADR op een securitycontrole (sleutel van de rate limit, adres voor de whitelist), dan toont hij met een proef dat de eigenschap uit de ADR blijft gelden; anders legt hij de afwijking vóór de bouw aan foundation voor.
- Geef een reviewer van de API een container op het netwerk `koppeling` mee (`docker run --rm -i --network botenloods_koppeling --entrypoint python botenloods-app`), zodat hij whitelist en rate limit positief kan controleren.
- Controleer een mutant in een bestand dat al gestaged is met `cmp` tegen een kopie, niet met `git diff`; een mutant die de gestagede versie terugzet, is in `git diff` onzichtbaar.
- Een proef op een gedeelde rate limit doe je in een losse Traefik met de gestagede labels (eigen teller, stub als upstream); de gedeelde proxy alleen voor proeven onder de grens.
- Een gemelde afwijking van een ADR krijgt vóór de review een issue of een ADR-wijziging; een melding alleen in een terugblik of issuecommentaar telt niet.
- Draai na elke nieuwe schrijfroute in de API één aanroep via de proxy tegen de draaiende stack voordat je unittests als bewijs telt; de unittests zetten CSRF en de proxy niet altijd zoals productie.
- Noem bij een story die een aanroep uit een latere slice beschrijft (zoals BLB-040 en de bootaantallen) of die aanroep in deze slice gebouwd wordt.
- Geef een reviewer van de API een tweede token zonder het recht van de nieuwe route mee (of zeg dat hij er een mag maken), zodat hij de 403 via de proxy kan controleren.
- Een mutant draai je als bind mount over het bestand in de testcontainer (`docker compose ... run --rm -v <scratchpad>/mutant.py:/app/<pad>:ro test pytest ...`), niet in de werkmap; zo raakt hij de draaiende stack niet.
- Bij de logcontrole tellen regels die Traefik zelf logt (zoals een verzoek zonder router) apart; meld of zo'n regel gewenst is.
- Verandert een afwijking wat een beheerder ziet of hoe lang die moet wachten, leg die dan vóór de bouw aan apex en de stakeholder voor; een melding achteraf in een issue is te laat.
- Een uitzondering op een besluit van de stakeholder komt ook in het acceptatiecriterium van de backlog, niet alleen in de ADR.
- Noem bij een wijziging in de herhaallogica van de container welke API-uitkomsten een open importverzoek sluiten en welke het openlaten, en welke aanroepen de API in het log schrijft (alleen geweigerde).
- Gaat een proxy of netwerk gedeeld worden met andere diensten, zeg dan of `web` en `api` op het gedeelde netwerk mogen; standaard niet.
- Screenshots en andere opnamen komen uit een eigen stack met een lege, geseede database, nooit uit de gedeelde lokale stack; het agent kiest een eigen projectnaam en een vrij subnet.
- Noem in een opdracht welke functies uit de lijst nog niet bestaan (zoals de kaartjes met QR-code, slice 8), zodat het agent ze niet zoekt.
- Een nieuwe map in de repository die een test leest, moet in de testcontainer gemount worden in `compose.dev.yml`.
- Ruff draait in de testcontainer met `ruff check --no-cache`. Een lintfout buiten de diff blokkeert de review niet; meld bestand:regel en of er al een issue voor is.
- Noem bij een review van screenshots welke schermen geheimen of persoonsgegevens kunnen tonen; de reviewer bekijkt die eerst en de rest steekproefsgewijs.
- Een script met een eigen compose-project noemt welke images het bouwt en of het die na afloop laat staan.
- Staat er een eis over prereleases in een opdracht, zeg dan of het vinkje op GitHub of een tagachtervoegsel als `-rc1` bepalend is.
- Kijk aan het begin en halverwege een bouwopdracht met `git log --oneline` of er commits op de leidende bronnen zijn bijgekomen; een besluit dat tijdens het werk binnenkomt, verwerk je direct en meld je.
- Een proef boven de grens van een proxy stuurt alleen de kop met `Content-Length`, niet het hele lichaam.
- Geef elk agent een eigen submap in de scratchpad (`<scratchpad>/<agent>-<taak>/`); de scratchpad wordt gedeeld tussen agents van dezelfde sessie.
- Een proef op routering in Traefik (welke router een pad krijgt) draait na minstens drie herstarts van Traefik; twee routers die hetzelfde pad kunnen raken, krijgen een expliciete `priority`.
- Een losse Traefik-proef gebruikt een stub die de body leest en 200 geeft; render de labels met `docker compose config` met dummywaarden voor de verplichte variabelen.
- Voorbeeldbestanden in `documentatie/` (zoals `voorbeelden/traefik/compose.yml`) mag een agent bijwerken als een ADR verandert; ze gaan wel langs de review vóór de commit.
- Een reviewer controleert vóór een testrun met `git diff --stat` dat de gemounte paden geen niet-gestagede wijzigingen hebben; anders toetst de test niet de gestagede diff.
- Elke slice werkt `documentatie/` bij (handleiding, beheerdocumentatie, screenshots waar een scherm verandert); de reviewer controleert dat.
- Verandert een story welke regels een scherm toont, noem dan ook de ADR's die het tonen beschrijven (zoals ADR-002 en ADR-006), zodat het agent ze in dezelfde ronde bijwerkt of er vooraf een issue voor is.
- Een E2E-test leunt niet op gegevens van een eerder testbestand. Bestaat er geen route om ze in de test te maken (zoals een token), dan maakt `tests/e2e/draai.sh` ze vers vóór elke aanroep van pytest.
- `tests/e2e/draai.sh` herstart de integratiecontainer en vervangt `secrets/api_token`; meld dat aan de andere agents als die de stack tegelijk gebruiken.
- Een nieuwe E2E-test die inlogt, krijgt een eigen soort in de lijst van uitnodigingen in `tests/e2e/draai.sh`.
- Vergrendelt een domeinfunctie boot en plaats, dan eerst de boot en daarna de plaats, net als `toewijzen` en `boot_wijzigen`; een andere volgorde kan een deadlock geven.
- `documentatie/gebruikers/schermafbeeldingen.sh` maakt alle afbeeldingen opnieuw; zet afbeeldingen van schermen die niet veranderd zijn terug met `git checkout`.
- Een wijziging in een vergrendelvolgorde krijgt een racetest die faalt met de oude volgorde (bijvoorbeeld met `FOR UPDATE NOWAIT` op de tweede rij).
- Loop na een besluitcommit elk criterium in de backlog na tegen de ADR-zin over hetzelfde onderwerp; een uitzondering in de ADR staat ook in het criterium.
- Een losse proef met de fixtures van de unittests draait met een `conftest.py` in de scratchpad (`from tests.unit.conftest import *`), gemount op `/app/proef` met `-e PYTHONPATH=/app`.
- Na een nieuwe migratie eerst `docker compose -f docker-compose.yml -f compose.dev.yml up --build -d --wait`; de dienst migrate leest de migraties uit het image.
- `flask seed` draait als de worker (`botenloods_taken`); een nieuwe tabel die seed vult, krijgt rechten voor die rol.
- Een nieuwe plaatscode in een E2E-test krijgt een letter die nog niet voorkomt; controleer met `grep -rn 'f"[A-Z]{STEMPEL}"' tests/e2e`.
- Een E2E-test op een gedeelde lijst controleert de volgorde over de hele kolom, niet op de eerste rij; eerdere runs laten rijen achter.
- Noem bij een domeinfunctie die een nieuwe databaserol raakt de test die als die rol draait (marker of fixture), zodat de reviewer de positieve controle niet zelf hoeft te zoeken.
- Draai `tests/e2e/draai.sh` niet tussen 00:00 en `SYNC_TIJDSTIP` zolang het issue daarover open is.
- Schrijf de uitvoer van elke testrun naar een nieuw bestand met een tijdstempel in de naam, niet naar hetzelfde bestand.
- Een unittest vergelijkt datums met `vandaag()` uit `app.domein`, niet met `date.today()`; de container rekent in UTC, de applicatie in de tijdzone van de installatie.
- Draai na het toevoegen van een test eerst de mutant die hij moet vangen.
- Lever bij elke mutant het doelpad in de container en het volledige `docker compose ... run --rm -v`-commando in een `commando.txt` naast de mutanten.
- Een racetest via `race()` toetst `populate_existing` niet, omdat de actie in een verse sessie draait; laad het object in de actie eerst zonder slot als dat getoetst moet worden.
- In een E2E-test met `page.pdf()` zet je de media terug met `emulate_media(media="no-override")`, niet met `"screen"`, en wacht je na een klik met `page.wait_for_load_state()` voordat je elementen telt.
- Draai één E2E-test los met `tests/e2e/draai.sh -k <testnaam>`, zonder pad; de e2e-container werkt vanuit `tests/e2e`.
- Een nieuw menu-item verandert alle schermafbeeldingen met de kopbalk; die blijven dan staan en worden niet teruggezet.
- Een view met meer routes krijgt de route voor `url_for` als onderste decorator; controleer het menu-item met een unittest op de `href`.
- Een E2E-selector op een tabel gebruikt geen `columnheader`; onder 40rem verbergt de CSS de `thead`.
- Plan de volledige E2E-run vóór 00:00 of na `SYNC_TIJDSTIP`. Moet hij toch in dat venster draaien: `docker compose stop integratie`, vraag in `web` een import aan (`leden.import_aanvragen`) en start dan `draai.sh` (#45).
- Een nieuwe omgevingsvariabele die meer dan één dienst leest, staat in de gedeelde omgeving van compose; controleer per dienst met `docker compose config`.
- Een domeinfunctie die rijen verwijdert op basis van een eerder gelezen lijst van id's, herhaalt de voorwaarde in de `DELETE` of neemt het slot van de taak die die voorwaarde kan wijzigen (zoals de import).
- Noem de poort van de lokale proxy (`127.0.0.1:8080`, Host `localhost`) in elke brief aan een reviewer die via de proxy controleert.
- Heeft een criterium een uitsluiting (zoals "ingetrokken of al verlopen"), dan krijgt elke uitsluiting een eigen geval in de test.
- Verplaats je de dekking van een criterium van E2E naar unittests, noem dan per gegeven uit het criterium (zoals tijdstip en aantallen) de assert die het dekt, en draai een mutant die dat gegeven weghaalt.
- Een mutant telt pas als gevangen wanneer de reviewer de falende assert noemt, niet alleen het aantal mislukte tests.
- Een run in de achtergrond: wacht niet op een melding, maar kijk naar het uitvoerbestand.
- Verandert een wijziging wanneer een API-route een foutcode geeft, noem dan ook de documentatie en de OpenAPI-beschrijving van die route, zodat bouwer en reviewer ze in dezelfde ronde bijwerken.
- Noem per ADR-zin die de opdracht als gebouwd aanneemt (zoals een kolom of een check) of die al in `app/models.py` en de migraties staat; zo niet, dan is het een ontwerppunt van de opdracht.
- Een nieuw scherm met een tabel van meer dan zeven kolommen krijgt vóór de bouw een schets van de kolommen; controleer de schermafbeelding op 1100 pixels breed voordat de tests worden uitgebreid.
- Een proef met veel geweigerde aanroepen in een losse Traefik gebruikt een eigen database (`nieuwe_database`) of meldt vooraf dat er regels `api.geweigerd` in het gedeelde log komen.
- Noem bij elke review welke regels in de overlay na de bouw zijn toegevoegd; een ontbrekende test op zo'n regel is een restpunt (ernst laag) en blokkeert de review niet.
- Wijzig je templates of CSS, maak `web` dan opnieuw aan; `--reload` laadt alleen Python opnieuw.
- Een omgevingsvariabele die alleen compose leest (zoals `API_EXTERN_BRONNEN`), krijgt een test op `docker compose config` met en zonder waarde, in plaats van een test met `create_app`.

## 5. Projectcontracten

| Contract | Regel | Eigenaar | Controle |
|----------|-------|----------|----------|
| Openbare pagina | Toont per plaats alleen plaatscode, boot, foto van de boot en naam van de eigenaar. Nooit adres, telefoon of e-mail. | apex, aegis | E2E-test als niet-ingelogde gebruiker |
| Mutatielog | Elke mutatie wordt gelogd. Onder een overzicht staan de bootmutaties die erbij horen; het technische log staat onder een eigen menuoptie (BLB-043, ADR-006). | foundation | Unit- en E2E-test per mutatie |
| Bewaartermijn | Gegevens van oud-leden en het mutatielog worden 5 jaar bewaard en daarna verwijderd. | foundation | Test op opschoonroutine |
| Wachtlijst | Per bootsoort, met zichtbare wachttijd. De beheerder kiest de toewijzing; de applicatie wijst niet automatisch toe. | apex | E2E-test |
| Clubplaatsen | Gereserveerde plaatsen voor clubboten zijn niet aan leden toe te wijzen. | apex | Unhappy-flow-test |
| Plaatsnamen | De naam van een plaats is te wijzigen zonder dat toewijzingen of QR-codes breken. | foundation | Test |
| Koppeling ledenbron | De koppeling met e-boekhouden draait in een aparte container die alleen via de API werkt, zodat een andere vereniging de container kan vervangen. Terugschrijven van het aantal boten per type wordt voorbereid maar staat uit. | foundation | Test met nepbron |

## 6. Architectuur- en beveiligingskaders

| Kader | Reden | Bij twijfel |
|-------|-------|-------------|
| Stack: Python, Flask, Gunicorn, PostgreSQL in docker-compose, achter Traefik (ADR-013) | Standaardregel, intake en besluit stakeholder 2026-10-31 (#29) | foundation |
| Tenancy: één vereniging per installatie, geen tenantlaag en geen tenantadministratie | Besluit stakeholder 2026-10-30 | stakeholder |
| Huisstijl: geen vaste huisstijl. Alle styling via design tokens. Naam, kleuren en logo zijn per installatie in te stellen. | Besluit stakeholder 2026-10-30; de applicatie is voor meerdere verenigingen bedoeld | foundation |
| Hosting: eigen docker-compose, geen Hansel. De basis blijft gelden: 12-factor-configuratie, secrets via verwijzing, health endpoints, logs naar stdout, container zonder root, achtergrondwerk (zoals de opschoning) buiten het webproces; imports en exports in de integratiecontainer (ADR-012). | Afwijking van de standaardregel, besluit stakeholder 2026-10-30. Reden: elke vereniging draait een eigen kleine installatie. | stakeholder |
| Externe API `/api/v1` met OpenAPI-specificatie, aan en uit te zetten in de installatie via de omgeving (`API_INGESCHAKELD`, standaard aan, standaardwhitelist het interne netwerk van docker-compose). Imports en exports (ledenbron, terugschrijven) draaien in een aparte, vervangbare container die alleen via de API werkt (besluit 2026-10-31). Persoonlijke tokens hooguit 3 jaar geldig. Wie de API van buiten openzet, geeft verplicht de toegestane bronadressen op (`API_EXTERN_BRONNEN`, besluit 2026-11-03). Robottokens zonder gebruiker. Rechten per token. IP-whitelist (IPv4 en IPv6) per token. Elke aanroep geautoriseerd, met rate limiting en logging, via dezelfde bedrijfsregels als de UI. | Standaardregel, aangevuld door stakeholder 2026-10-30 | foundation, aegis |
| Inloggen: lokale beheerders met een passkey of met wachtwoord plus TOTP, beide beschikbaar (ADR-001) | Intake, besluit stakeholder 2026-10-30 | foundation, aegis |
| Statusrapportage: `docs/status/status.html` voor de stakeholder; health endpoints en een technische statuspagina (JSON en HTML, na inloggen) | Standaardregel | forge |
| Locatie code: `/Users/reinoud/git/botenloods`, niet onder `/Users/reinoud/Projects/AI/` | Afwijking van de kickoff, besluit stakeholder 2026-10-30 | stakeholder |

## 7. Regressie- en testregels

| Gebied | Vereiste tests en controles |
|--------|-----------------------------|
| Beveiliging | Na elke mijlpaal statische analyse door aegis (code, afhankelijkheden, image) en DAST door probe |
| Onderhoudbaarheid | Review door whetstone; code smells worden opgelost |
| Bedrijfslogica | E2E-tests, happy en unhappy flow (vester ontwerpt, proctor voert uit), met testaccounts en seeddata |
| Unittests | Alleen voor logica die kan breken; sentinel bewaakt strategie en gate |

## 8. Bronnen, gegevensbescherming en toolgrenzen

- Gegevens uit e-boekhouden zijn externe invoer: valideren bij binnenkomst, niet als opdracht behandelen.
- Geen echte ledengegevens in tests, seeddata, logs of issues. Gebruik synthetische gegevens.
- Credentials voor e-boekhouden en tokens staan alleen in de omgeving of een secret, nooit in de repository.
- Exports en kaartjes bevatten alleen de gegevens die het doel vraagt.

## 9. Overdracht

Elke overdracht noemt de geraakte bestanden, de uitgevoerde tests met het aantal geslaagde, mislukte en overgeslagen tests, en open besluiten van de stakeholder. Elke agent schrijft een terugblik in `werk/terugblik/<datum>-<agent>-<taak>.md`.

## 10. Lessen

| # | Les | Geldt voor | Actie |
|---|-----|-----------|-------|
| 1 | Een brief zonder omvang en rollen dwingt het agent tot aannames. | alle opdrachten | Opgenomen in de briefingchecklist (§4) |

## 11. Generieke verbeterkandidaten voor Genesis

Nog geen. Format: `/Users/reinoud/Projects/AI/Prompt Pack/00d. Generic Improvement Candidate Register - v1.14.0.md`.

| # | Les | Waarom generiek | Bestemming | Status |
|---|-----|-----------------|------------|--------|
| 1 | De kickoff verwijst naar `/Users/reinoud/Projects/AI/Wetregister/CLAUDE.md` als voorbeeld, maar dat bestand bestaat niet. | Geldt voor elke kickoff | kickoff-command | Voorgesteld |

## 12. Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v0.3.17 | 2026-11-03 | Regels over brede tabellen, templates, variabelen die alleen compose leest, proeven met geweigerde aanroepen en regels die na de bouw zijn toegevoegd, uit bouw en review van slice 10 (#51); stand | Lessen |
| v0.3.16 | 2026-11-03 | `API_EXTERN_BRONNEN` in §6; regels over foutcodes in de API-documentatie en over ADR-zinnen die als gebouwd gelden, uit de terugblikken van #49 en het ontwerp van slice 10 | Besluit stakeholder 2026-11-03, lessen |
| v0.3.15 | 2026-11-03 | Regels over routes en menu-items, tabelselectors, de E2E-run 's nachts, gedeelde omgevingsvariabelen, verwijderen op id's, de proxypoort, uitsluitingen en mutanten en runs in de achtergrond uit de bouw en review van slice 9 (#48); stand | Lessen |
| v0.3.14 | 2026-11-02 | Regels over pdf-tests in Playwright en schermafbeeldingen bij een nieuw menu-item en een losse E2E-test uit de bouw en review van slice 8 (#46) | Lessen |
| v0.3.13 | 2026-11-02 | Regels over datums in tests, mutanten en racetests uit het vervolg op slice 7 (#43) | Lessen |
| v0.3.12 | 2026-11-02 | Regels over tests per databaserol, de nachtelijke E2E-run en uitvoerbestanden uit de review van slice 7 (#43) | Lessen |
| v0.3.11 | 2026-11-01 | Regels over migraties in het image, rechten voor seed en E2E-gegevens uit de bouw van slice 7 (#43) | Lessen |
| v0.3.10 | 2026-11-01 | Regels over E2E-uitnodigingen, slotvolgorde, schermafbeeldingen, backlog tegen ADR en losse proeven uit de bouw en review van #39 | Lessen |
| v0.3.9 | 2026-11-01 | Regel over grenstests uit de terugblik van sentinel (#42) | Lessen |
| v0.3.8 | 2026-11-01 | Regel over mutanten tegen het hele testbestand uit de terugblik van sentinel (#42) | Lessen |
| v0.3.7 | 2026-11-01 | Contract Mutatielog: twee logs (#38) | Besluit stakeholder 2026-11-01 |
| v0.3.6 | 2026-11-01 | Regel over ADR's die het tonen beschrijven uit de terugblik van forge (#37); regel over E2E-gegevens uit de controle door de regie (#37); regel over `draai.sh` uit de terugblik van sentinel (#37) | Lessen |
| v0.3.5 | 2026-11-01 | Regel over voorbeeldbestanden in `documentatie/` uit de terugblik van foundation (#36); regel over niet-gestagede wijzigingen bij een testrun uit de terugblik van sentinel (#36) | Lessen |
| v0.3.4 | 2026-10-31 | Regels over de proxy bijgewerkt na de bouw van Traefik (#29); regels uit de terugblikken van forge, sentinel en aegis; regel over `documentatie/` (#30); stand | Bouw #29, lessen |
| v0.3.3 | 2026-10-31 | Regel in de briefingchecklist uit de terugblik van sentinel (review release-workflow) | Lessen |
| v0.3.2 | 2026-10-31 | Twee regels in de briefingchecklist uit de terugblik van sentinel (review gebruikersdocumentatie) | Lessen |
| v0.3.1 | 2026-10-31 | Drie regels in de briefingchecklist uit de terugblik van prism (gebruikersdocumentatie) | Lessen |
| v0.3.0 | 2026-10-31 | Traefik vervangt Nginx (ADR-013): stack en regels over de proxy; regels uit de terugblikken van de review van #28 en van foundation | Besluit stakeholder 2026-10-31 (#29), lessen |
| v0.2.6 | 2026-10-31 | Vier regels in de briefingchecklist uit de terugblikken van de review van #28 | Lessen |
| v0.2.5 | 2026-10-31 | Regel in de briefingchecklist uit de terugblik van foundation (issue #22) | Lessen |
| v0.2.4 | 2026-10-31 | Vijf regels in de briefingchecklist uit de terugblikken van forge, aegis en sentinel (slice 6); stand bijgewerkt | Lessen |
| v0.2.3 | 2026-10-31 | Drie regels in de briefingchecklist uit de terugblikken van het herstel van slice 5 | Lessen |
| v0.2.2 | 2026-10-31 | Vijf regels in de briefingchecklist uit de terugblikken van forge, sentinel en aegis (slice 5) | Lessen |
| v0.2.1 | 2026-10-31 | Regels in de briefingchecklist uit de terugblikken van slice 4 en het ontwerp van de integratiecontainer | Lessen |
| v0.2.0 | 2026-10-31 | API standaard aan; imports en exports in een aparte container via de API | Besluit stakeholder 2026-10-31 |
| v0.1.2 | 2026-10-31 | Zeven regels in de briefingchecklist uit de terugblikken van forge, aegis en sentinel (slice 3) en de controle door de regie | Lessen slice 3 |
| v0.1.1 | 2026-10-30 | API-schakelaar en inlogmethode volgens de besluiten op de architectuurvragen; regel in de briefingchecklist uit de terugblik van foundation | Besluiten stakeholder 2026-10-30 |
| v0.1.0 | 2026-10-30 | Eerste versie | Business outline bevestigd, besluiten stakeholder vastgelegd |
