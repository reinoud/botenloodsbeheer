# Projectoverlay botenloodsbeheer

**Project:** botenloodsbeheer
**Geldt voor:** alle agents in dit project
**Versie overlay:** v0.5.75
**Beheer:** regie (hoofdsessie), na akkoord van de stakeholder
**Status:** concept
**Bijgewerkt:** 2026-11-12

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
| Omvang | 11 rekken en 229 plaatsen (de echte indeling, #80), ongeveer 210 leden en 180 boten. |
| Stack | Python, Flask, Gunicorn en PostgreSQL, in docker-compose, achter Traefik (ADR-013). |
| Gevoeligheid van gegevens | Persoonsgegevens van leden en oud-leden (lidnummer, naam, lidmaatschapsdata). Adres, telefoon en e-mail worden niet bewaard (#180). Openbaar alleen de naam van de eigenaar en de foto van de boot, met instemming van de leden. |
| Bron van leden | e-boekhouden, via een aparte en vervangbare integratiecontainer die alleen via de API werkt (ADR-012). Leden worden niet in de applicatie beheerd. |
| Uitrol | Eigen docker-compose per vereniging. |
| Stand | Slice 1 tot en met 12 gebouwd; de indeling volgt rek, verdieping en vak (#80). Traefik vervangt Nginx (#29). Gebruikers- en beheerdocumentatie in `documentatie/` (#30). |

## 4. Werkwijze

- Volgorde: apex (backlog en user stories), foundation (architectuur en ADR's), forge (delivery in slices).
- Open werk staat in GitHub-issues van `reinoud/botenloodsbeheer`, met dezelfde regels als de Forgejo-afspraak in `~/.claude/CLAUDE.md`: type en label, sluiten met commit, test en bewijs.
- Review vóór elke codecommit volgens `~/.claude/CLAUDE.md`. Voor inloggen, tokens, autorisatie en de koppeling met e-boekhouden reviewt aegis mee.
- Elke feature, bug of taak met code komt in een eigen branch van `main` (`feature/<issue>-<kort>`, `fix/<issue>-<kort>`). De review vóór de commit gebeurt op die branch. Na akkoord van de reviewers en een geslaagde testsuite pusht de sessie de branch en opent een pull request naar `main` met `gh pr create`; de beschrijving noemt het issue (`Closes #<nr>`), de reviewers met hun oordeel en de testuitkomst. Zet het slotcommentaar (gewijzigd, getest, bewijs) vóór de merge op het issue: `Closes` sluit het issue bij de merge zonder commentaar. Is een criterium pas na de merge te toetsen (zoals Dependabot), gebruik dan `Refs #<nr>` in plaats van `Closes` en sluit het issue zelf na die controle. De sessie mag dat pull request zelf mergen (`gh pr merge --squash --delete-branch`), zoals eerder de push naar `main`; GitHub laat de auteur geen eigen goedkeuring geven, de review van de agents geldt als vierogenprincipe. Commits met alleen documentatie mogen tot de beveiliging van `main` nog direct op `main`; daarna gaan ook die via een pull request. Een force-push en het verwijderen van andere branches dan de eigen, gemergde branch vragen akkoord. Besluit van de stakeholder, 2026-11-05.
- Elk agent dat code schrijft of reviewt, gebruikt de skill `ponytail`.
- Teksten volgen de skill `schrijfstijl`.
- Elke open pull request van Dependabot krijgt een issue (`taak`, `dependencies`), tenzij er al een is. Het issue noemt wat de PR mist, zoals een pakketversie die niet meebeweegt. Besluit van de stakeholder, 2026-11-05.
- Normenbibliotheek: `/Users/reinoud/Projects/AI/01. Standaarden/`. Raadplegen mag, kopiëren niet.
- Werk gebeurt in milestones die de regie met de stakeholder afstemt. Vóór een milestone legt de regie een voorstel voor: de issues, de volgorde, wat af betekent en wat er bewust buiten valt. Pas na akkoord start het werk. Binnen een afgestemde milestone werkt de regie door zonder tussenakkoord; een nieuw issue dat tijdens het werk ontstaat, gaat naar de volgende afstemming en niet stil de milestone in, tenzij het de milestone zelf blokkeert. Na de milestone meldt de regie de uitkomst en stelt de volgende voor. Besluit van de stakeholder, 2026-11-10.

### Briefingchecklist

De regie loopt deze lijst na bij elke agentopdracht: altijd het deel Algemeen, daarna de delen die bij de soort opdracht horen.

#### Algemeen (elke brief)

- Geef bij elke agentopdracht model en effort expliciet mee (besluit stakeholder, 2026-11-06). Reviews (sentinel, aegis): Opus 5.5 met effort `higher`. Bouw (prism, bedrock en andere bouwers): Sonnet 5.5, effort standaard. Mechanische opdrachten die zichzelf controleren (zoeken en rapporteren, een vaste reeks stappen nalopen): effort `lower`. Een grote review (meer dan 50 bestanden of een migratie) krijgt altijd `higher`.
- Geef de omvang (11 rekken, 229 plaatsen, 210 leden, 180 boten) en de rollen (3 gelijke beheerders, geen systeembeheerrol) mee.
- `docs/business/intake.md` is leidend boven de business outline en boven eigen inschatting.
- Noem een ADR bij nummer en bestandsnaam zoals `ls docs/architecture/adr/` die toont, niet met een omschrijving uit het hoofd.
- Geef bij een omvang het woordbudget per onderdeel, niet alleen een totaal. Een woordgrens voor een alinea telt alleen de alinea; kop, versieregel en wijzigingslog tellen apart.
- Zeg welke open vragen blokkerend zijn, of laat het agent dat expliciet per vraag markeren.
- Noem de overlayregels uit §4 die op een proef van toepassing zijn, en zeg per regel of de proef er in dit issue aan moet voldoen of dat het een restpunt mag worden.
- Tel een woordbudget voor nieuwe of gewijzigde tekst met `git diff --word-diff=porcelain <bestand> | grep '^+[^+]' | wc -w`; `wc -w` op de plusregels telt ongewijzigde woorden in aangepaste regels mee.
- Noem bij elk besluit in de bron of het in deze ronde verwerkt moet worden; een besluit dat niet genoemd is, komt als open vraag terug.
- Noem welke ongecommitte bestanden (model, migratie) nog een oud besluit bevatten, zodat het agent ze als ontwerppunt meeneemt.
- Haal een issue op met `gh issue view <nr> -R reinoud/botenloodsbeheer --json title,body,comments`; `--comments` alleen toont de tekst van het issue niet.
- Zoek vóór een besluit met `grep -rn` naar elke instelling die het besluit raakt (zoals `PROXY_HOPS` of `ipStrategy`) in `docs/`, `documentatie/` en `.env.example`, en noem elk gevonden bestand als te raken bestand of als verouderde regel.
- Zoek in issues naar een versienummer of een andere term met een punt met `gh issue list --json number,title,body --jq`, niet met `--search`; de zoekfunctie van GitHub vindt zulke termen niet betrouwbaar.
- Noem een criterium met zijn tekst of met de versie van de backlog erbij, niet alleen met een nummer.
- Wijkt de bouw bewust af van een acceptatiecriterium, pas dan vóór de review het criterium in het issue aan en noem de bron die voorgaat.
- Geef elk agent een eigen submap in de scratchpad (`<scratchpad>/<agent>-<taak>/`); de scratchpad wordt gedeeld tussen agents van dezelfde sessie.
- Tekstwijzigingen in bestanden met python3, niet met sed (de sed-variant verschilt per omgeving).
- Heeft het document geen wijzigingslog, maak dan een paragraaf Wijzigingslog aan met alleen de nieuwe versie.
- Noem in een opdracht welke functies uit de lijst nog niet bestaan (zoals de kaartjes met QR-code, slice 8), zodat het agent ze niet zoekt.
- Noem per ADR-zin die de opdracht als gebouwd aanneemt (zoals een kolom of een check) of die al in `app/models.py` en de migraties staat; zo niet, dan is het een ontwerppunt van de opdracht.
- Kijk bij een bouwopdracht aan het begin en halverwege met `git log --oneline` of er commits op de leidende bronnen zijn bijgekomen, en draai vóór elke oplevering `git diff` op die bronnen. Een besluit dat tijdens het werk binnenkomt, gaat voor de opdracht: verwerk het direct en meld het in je antwoord.
- Staat er een eis over prereleases in een opdracht, zeg dan of het vinkje op GitHub of een tagachtervoegsel als `-rc1` bepalend is.
- Noem in een reviewbrief de niet-gestagede bestanden in de werkmap (`git status --short`, tweede kolom) en of de review ze negeert.
- Commit alleen de gereviewde paden; parallelle agents wijzigen documenten in dezelfde werkmap.
- Noem bij een filter op tekst uit een externe bron de waarden die in de praktijk voorkomen, of zeg dat ze onbekend zijn, zodat bouwer en reviewer weten of "begint met", "bevat" of "is gelijk aan" bedoeld is.
- Noem bij een filter op externe invoer of hoofdletters en witruimte vóór de waarde meetellen, en welke test elk randgeval dekt.
- Staat een filter in een gedeelde functie zodat meer aanroepers hetzelfde gedrag krijgen, dan heeft elke aanroeper een test met het nieuwe geval; noem die tests in de brief.
- Een subagent levert zijn uitkomst via de hand-back; vraag geen SendMessage naar `main` (dat kanaal heeft hij niet). Alleen een teammate stuurt naar `main`, nooit naar `team-lead`.
- Noem bij een tekstwijziging voor gebruikers de handleiding met pad: `documentatie/gebruikers/handleiding.md`.
- Geef bij een externe SOAP-dienst de WSDL vooraf mee in de scratchpad, en noem het adresschema (http of https) dat de dienst gebruikt.
- Kiest een besluit een bibliotheek, controleer dan vóór het besluit in de broncode van de vastgepinde versie dat elke nodige aanroep bestaat, voor lezen én schrijven, en noem die aanroepen in de opdracht.
- Wordt een pakket of afhankelijkheid vervangen, zoek dan ook in `docs/status/status.html` en in open issues naar de oude naam, en werk die in dezelfde ronde bij.

#### Bouw

- Versmalt een besluit een weigering, noem dan elk geval dat van fout naar geaccepteerd gaat (ook buiten het issue), met per geval of er een test en een zin in de handleiding komt. Laat de bouwer eerst in `tests/` zoeken op de oude melding en de tests noemen die hij omzet.
- Controleer vóór een bouwopdracht of Docker draait, en noem in de opdracht welke images al lokaal staan.
- Losse controles in Python draaien met `docker compose exec -T web python -c ...`, niet in de lokale `.venv`; dat geldt ook voor reviewers. Een los controlescript in de testcontainer draai je met `-e PYTHONPATH=/app` en een volume uit de scratchpad. Een proef met de fixtures van de unittests krijgt daarbij een `conftest.py` in de scratchpad (`from tests.unit.conftest import *`), gemount op `/app/proef`.
- Bewerk geen Python-bestanden in de werkmap terwijl een reviewer de log van `web` en `api` controleert (`--reload` laadt halve bestanden); noem het tijdstip van de laatste `up --build` in de brief.
- Wijzig je templates of CSS, maak `web` dan opnieuw aan met `docker compose -f docker-compose.yml -f compose.dev.yml up -d --no-deps --force-recreate web`, nooit zonder `compose.dev.yml` (dan leidt `:8080` om naar https en valt de hele E2E-suite); `--reload` laadt alleen Python opnieuw. Controleer vóór een E2E-run met `docker inspect -f '{{index .Config.Labels "com.docker.compose.project.config_files"}}' botenloods-web-1` dat `web` met `compose.dev.yml` draait. Na een wijziging of `up --build` die `web`, `api` of `integratie` opnieuw aanmaakt, wacht je tot de containers healthy zijn voordat je E2E-tests of curl-controles draait; tot dan geeft Traefik 404. Een herstart van de proxy is niet nodig.
- Een nieuwe map in de repository die een test leest, moet in de testcontainer gemount worden in `compose.dev.yml`.
- Draai geen compose-commando terwijl een `git stash` actief is; vergelijk een baseline in een aparte worktree.
- Een script met een eigen compose-project noemt welke images het bouwt en of het die na afloop laat staan.
- Verandert een wijziging de naam van een image, noem dan in de brief of het oude image nog op de host staat en wie het opruimt.
- Een afwijking van een ADR die alleen namen of de plaats van een instelling raakt (zoals een omgevingsvariabele per dienst), mag het bouwende agent doorvoeren en melden; foundation werkt de ADR daarna bij. Elke gemelde afwijking krijgt vóór de review een issue of een ADR-wijziging; een melding alleen in een terugblik of issuecommentaar telt niet. Verandert een afwijking wat een beheerder ziet of hoe lang die moet wachten, leg die dan vóór de bouw aan apex en de stakeholder voor; een melding achteraf in een issue is te laat.
- Elke nieuwe omgevingsvariabele krijgt een test die de variabele zet en `create_app` aanroept (geldige en ongeldige waarde); een test die alleen `app.config` overschrijft, telt niet. Leest alleen compose de variabele (zoals `API_EXTERN_BRONNEN`), dan komt er in plaats daarvan een test op `docker compose config` met en zonder waarde. Die controle staat bovenin `tests/e2e/draai.sh` en draait op de host, want de testcontainer heeft geen docker. Leest meer dan één dienst de variabele, dan staat hij in de gedeelde omgeving van compose; controleer per dienst met `docker compose config`.
- Noem bij een seed of fixture welke regel voorgaat als architectuur §6.3 botst met een ADR (standaard: de ADR).
- Geef bij een geplande taak aan hoe vaak die na een fout opnieuw mag proberen.
- Noem bij een wijziging in de herhaallogica van de container welke API-uitkomsten een open importverzoek sluiten en welke het openlaten, en welke aanroepen de API in het log schrijft (alleen geweigerde).
- Een logveld met de naam `code`, `adres`, `telefoon` of `email` staat in het log als `gewijzigd`; kies een andere sleutel als de waarde zichtbaar moet zijn.
- Geef een nieuwe webmodule geen naam die al bestaat in `app.web` (zoals een domeinmodule of functie); controleer na het toevoegen dat de route bestaat met `flask routes` of een unittest. Een view met meer routes krijgt de route voor `url_for` als onderste decorator; controleer het menu-item met een unittest op de `href`.
- Een nieuw scherm met een tabel van meer dan zeven kolommen krijgt vóór de bouw een schets van de kolommen; controleer de schermafbeelding op 1100 pixels breed voordat de tests worden uitgebreid.
- Beperkt een wijziging de invoerformaten, zeg dan in de brief welke melding de gebruiker daarna ziet.
- Een unittest vergelijkt datums met `vandaag()` uit `app.domein`, niet met `date.today()`; de container rekent in UTC, de applicatie in de tijdzone van de installatie.
- Een test met `filterwarnings("error")` noemt de categorie van de waarschuwing, zodat waarschuwingen uit andere tests hem niet laten falen. Een geparametriseerde test met binaire of grote invoer krijgt `ids=`.
- Heeft een criterium een uitsluiting (zoals "ingetrokken of al verlopen"), dan krijgt elke uitsluiting een eigen geval in de test.
- Noem bij een grenstest beide kanten van de grens met de testnaam die elke kant dekt. Een test op een grens (grootte, aantal, duur) gebruikt invoer die zonder die grens geldig is, en de mutant zonder de grens moet falen.
- Draai na het toevoegen van een test eerst de mutant die hij moet vangen, ook bij een nieuwe E2E-vergelijking, en meld pas daarna groen.
- Een controle op een reeks statuscodes toetst ook de herkomst van elke code (applicatie of Traefik), niet alleen de code.
- Noem bij een telling met de waarde 0 in het bewijs of die 0 verwacht is, en waarom.
- Noem bij elke nieuwe E2E-assertie de mutant die hij moet vangen, of zeg dat de E2E-test niet gemuteerd wordt.
- Controleer of elke letter van `reknaam()` in `tests/e2e/` uniek is met `grep -onE 'reknaam\([^)]*\)' tests/e2e/*.py`; dezelfde letter voor het rek en de bootnaam binnen één test telt niet als dubbel.
- Verandert een validatieregel in het domein, draai dan eerst de volledige unitsuite: die geeft de lijst van tests en E2E-helpers die met de oude regel gegevens maken.
- Noem bij een volgordetest elke sorteersleutel en zeg per sleutel of een mutant die hem weglaat moet vallen.
- Vervang je een aanroep op meer plekken door een gedeelde functie, draai dan per aanroep een mutant die de oude aanroep terugzet, en noem per aanroep de test die valt of waarom de mutant gelijkwaardig is.
- Werken twee agents tegelijk met unittests, dan draait elk op een eigen testdatabase (bind mount van een `conftest.py` met een andere `TEST_DB`); de gedeelde `botenloods_test` geeft anders een deadlock. Een racetest met `race()` controleert ook dat de actie geen andere uitzondering dan `Regelfout` gooit.
- Een nieuwe webroute krijgt als vaste afwerklijst: het menu-item, een rij in de routetabel van de handleiding (`test_handleiding_noemt_elke_webroute`) en een uitnodigingssoort in `tests/e2e/draai.sh`.
- `Plaats.bootsoorten` staat op id gesorteerd; "eerste soort" is de laagste id, niet de volgorde van aanvinken. `plaats()` in `tests/unit/hulp.py` weigert een lege soortenlijst; een plaats zonder soort maak je via `rek_aanmaken`.
- Verandert een wijziging de volgorde of weergave op één scherm, noem dan de andere schermen die hetzelfde gegeven tonen en of die bewust ongewijzigd blijven.
- Een bron buiten de repository (zoals designsystem) wordt gelezen op een genoemde commit, met `git show <commit>:<pad>`; de werkboom telt niet. Draai na een afname van de Dajaks-basis vóór de oplevering `python3 basis/controleer_product.py <repo> --doel app/web/static/ds --ref main` vanuit designsystem en meld de uitkomst; bestanden die niet uit de afname komen, staan buiten die map.
- Wijzigt de HTML-structuur (zoals een wrapper om een tabel), zoek dan eerst met `grep -rn` naar CSS-selectors in `tests/e2e/` die op de structuur leunen (`main > table`, `h2 + p + table`, `section.kaart`) en noem ze. Controleer een scherm ook op 360 pixels breed.
- Een nieuwe macro of een gewijzigd sjabloon dat gebruikersinvoer toont, krijgt een unittest met `<b>x</b>` die de geëscapete vorm toetst; de mutant met `|safe` op dat veld moet falen. Een fonttest controleert familie plus gewicht.
- Een test op het aantal migratieheads gebruikt de fixture `database` niet, zodat een tweede head op de eigen assert valt.
- Een wachtlus op een achtergrondproces gebruikt `docker ps` of een pidbestand, niet `pgrep -f` met de naam van het script in de eigen opdracht.
- Noem bij een nieuwe plaats of een nieuwe plaatsinvoer de beginwaarden (bootsoorten, clubplaats), zodat de E2E-helpers de juiste stappen krijgen.
- Noem bij elke wijziging van de signatuur van een domeinfunctie alle aanroepers (web, `app/seed.py`, `tests/unit/hulp.py`).
- Een nieuwe parameter van een domeinfunctie die een webroute via `uitvoeren()` aanroept, gaat als keyword via `functools.partial`; `uitvoeren` zet de actor als laatste positionele argument.
- Sluit een agentopdracht af met het eindrapport als laatste bericht; een terugblik in een bestand vervangt het rapport niet.
- Bewerk geen bestanden die een lopende testrun leest (handleiding, ADR) tot die run klaar is, en draai de documentatietest na de laatste tekstwijziging opnieuw.
- Draai de volledige unitsuite vlak vóór de oplevering opnieuw en meld ook errors (niet alleen failures). Een test die los slaagt maar in de suite een error geeft, telt niet als geslaagd.
- Schrijf de uitvoer van elke testrun naar een nieuw bestand met een tijdstempel in de naam. Bij een run in de achtergrond wacht je niet op een melding, maar kijk je naar het uitvoerbestand en naar `docker ps`; bij een subagent komt de melding vaak niet aan. Zet deze regel letterlijk in elke bouwopdracht.
- Draai vóór de bouw de E2E-suite op `main` en noem de bekende rode of wisselvallige tests in de opdracht.
- Noem in een bouwopdracht het commando voor de unitsuite: `docker compose -f docker-compose.yml -f compose.dev.yml run --rm --no-deps test pytest -q` (dienst `test`). Faalt een E2E-test in de volledige run, herhaal hem dan eerst los met `draai.sh -k`.
- Controleer of een schermafbeelding van het scherm bestaat voordat de opdracht haar opnieuw laat maken.
- `schermafbeeldingen.sh` maakt alle afbeeldingen opnieuw. De bouwer zet daarna alles behalve de afbeeldingen van het eigen scherm terug met `git checkout`.
- Noem bij een grens op bestandsgrootte of aantal regels of die ook voor het framework geldt: CSRFProtect leest het formulier tot `UPLOAD_MAX` voordat de route draait.
- Een import of export volgt de regels van de schermactie die dezelfde gegevens wijzigt. Noem in de opdracht die functie en haar test (bijvoorbeeld `_soorten` en `tests/unit/test_plaats_wijzigen_en_vrijgeven.py`), en laat het agent bij elke kolom beslissen wat een lege waarde betekent, voor een nieuw en een bestaand record.
- Test een rondgang (export, ongewijzigd importeren) ook met elke toestand die het scherm toelaat, zoals een plaats zonder bootsoort, en niet alleen met de standaardwaarden van de testhulpfuncties.
- Verandert een herstel een regel die ook in een gebruikerstekst staat (sjabloon, handleiding, ADR, schermuitleg), noem dan elke plek met bestand:regel en werk ze in dezelfde ronde bij.
- Een opdracht met een nieuw scherm noemt ADR-002 (Styling) en de designsystem-repository op een genoemde commit. De regie laat de schermen vóór de review toetsen door de sessie Design System.
- Noem bij een nieuw scherm of een nieuwe knop de linktekst. Die mag geen deel zijn van een bestaande link- of knoptekst op dezelfde pagina; Playwright `get_by_role(name=...)` zoekt op een deel van de tekst.
- Een testhulp die de database als eigenaar wijzigt (`eigenaar()`), doet daarna `db.session.expire_all()`; anders ziet de test oude waarden.
- Een test met de rol van de worker kan `beheerder` niet lezen. Zet testgegevens voor die rol met één SQL-regel als eigenaar (met een subselect), niet met een aparte leesactie.
- De werkmap is gemount in `web`: een sjabloonwijziging werkt direct door in een lopende E2E-run. Draai de baseline op `main` vóór je iets wijzigt, of in een aparte worktree.
- Zeg in de opdracht of de baseline op `main` in een aparte worktree draait of dat de bouwer de ongeveer 15 minuten wacht; tot de baseline klaar is, ligt de werkmap vast.
- Een visuele controle van een bezette plaats met foto vraagt een foto in de lokale database; de seed heeft er geen. Noem in de opdracht hoe de bouwer er een koppelt en weer weghaalt, of laat een unittest met foto volstaan.
- Haalt een wijziging een veld, element, tekst of kop uit een sjabloon, zoek dan in heel `tests/` (ook `tests/unit/`) naar de naam of de tekst (`grep -rn 'data-veld=<naam>\|"<naam>"' tests/`) en noem elke vindplaats; de regie doet dat ook bij een eigen kleine wijziging, en draait daarna de volledige unitsuite, niet alleen het eigen testbestand.
- Een mutant via tekstvervanging gebeurt met python3, met een assert dat de kopie verschilt van het origineel; een mutant die niet is toegepast, laat alles slagen.
- Een nieuwe `if` met meer voorwaarden krijgt per voorwaarde een eigen mutant die alleen die voorwaarde weglaat, met de assert die valt; een mutant die de hele regel uitzet, telt niet voor de afzonderlijke voorwaarden. Dat geldt ook voor een herstel door de regie.
- Neemt een agent een gestopte bouw over, noem dan in de opdracht welke teststappen al groen zijn, met het pad van de uitvoer, en welke niet bekend zijn.
- Tests van de integratiecontainer die `zeep` nodig hebben, draaien met `docker compose -f docker-compose.yml -f compose.dev.yml --profile test run --rm --no-deps --build test-integratie`; het test-image van `app` heeft geen zeep.
- Maak mutantkopieën in een map met een unieke naam (met tijdstempel) in de scratchpad, zonder `rm -rf`. Een boot van een oud-lid maak je in een test met een directe insert van `Boot`; de helper `boot()` weigert een oud-lid.
- Een mutantrun muteert bronbestanden in de werkmap. Niemand anders bewerkt die bestanden tijdens de run; draai mutanten altijd op een kopie die over het testimage gemount is, ook met een eigen script. Voor één bestand volstaat `-v <scratchpad>/<bestand>:/app/<pad>:ro` op `docker compose run`; een kopie van de hele repository is dan niet nodig.
- Noem bij een geweigerde actie (upload, formulier) per scherm of het blok daarna al open gaat; zo niet, zeg of het in dit issue open moet.
- Hangt een melding af van een toestand (zoals een vorige afbeelding), noem dan bij elke bestaande en nieuwe test welke toestand geldt.
- Een live proef die eigen testgegevens maakt (zoals een boot), ruimt die zelf op met een domeinfunctie; `opruimen.sql` kent alleen de stempelaccounts.
- Noem bij elke toestand die zonder JavaScript open moet staan (zoals een blok na een actie) het mechanisme: querystring, sessie of flash.
- Een schermafbeelding met `hoogte=` moet de nieuwe inhoud halen; bekijk elke nieuwe afbeelding.
- Noem bij een upload de router in Traefik met de grens op de grootte; een route buiten `/boten` valt onder de 1 MB van de algemene router. Test via Traefik met een geldig bestand boven 1 MB.
- Een E2E-test die globale staat zet (logo, naam), herstelt die in `finally`; vóór een mutantrun van zo'n test controleert de bouwer de beginstand.
- Een racetest voor `FOR UPDATE` laat de eerste sessie dezelfde wijziging doen als de functie; een lege `UPDATE` laat de mutant zonder `FOR UPDATE` slagen.
- Noem bij een nieuwe soort in een gedeelde tabel (zoals `afbeelding`) welke bestaande routes en taken die tabel lezen of opschonen.
- Noem bij het verwijderen van een recht of kolom welke databasecontroles (zoals `minstens_een_recht`) de migratie kunnen blokkeren en wat er gebeurt met rijen die ze raken; zoek ook tests met een aantal in de naam of `len(`-asserties op de lijst.
- Zoek E2E-selectors in alle bestanden van `tests/e2e/` en in `documentatie/gebruikers/schermafbeeldingen.py`, zonder bestanden uit te sluiten.
- Een CSS-regel die de bouwer met een reden afwijkend van het ontwerp toevoegt, krijgt een test die zonder die regel faalt, of de melding dat de seed het geval niet bevat (dan een issue). Meld de afwijking aan Design System.
- Vervangt een `ds-tag` of andere klasse uit de basis een eigen klasse (zoals `status-vrij`), noem dan de unittests die op de oude klasse toetsen.
- Noem bij een reeks zoekstappen (zoals lidnummer, koppeling, naam) wat een onbekende waarde in een stap doet: doorvallen naar de volgende stap of een fout.
- Elk antwoord uit een toets van Design System krijgt een eigen unittest en een mutant, ook zonder preview. Noem in de opdracht welke ontwerpkeuze geldt voor een toestand die de README niet noemt, en welke toestanden uit eerdere issues (zoals #137) een nieuwe tak in een sjabloon anders toont.
- Een `|safe`-mutant krijgt een testgeval per tak van het sjabloon die het veld toont, ook in een attribuut als `alt` (dan met een foto in de test).
- Een bouwer met mutanten controleert vóór de oplevering met `ls` dat `commando.txt` naast de mutanten staat. Draai een reeks mutanten met `docker compose run --rm -T` en `</dev/null` in een `while read`-lus.
- Meet een basislijn of uitlijning aan het begin van de eerste regel van elk element, niet aan het einde van de tekst.
- Draai de unitsuite in een worktree met `docker compose -p botenloods --env-file <hoofdwerkmap>/.env ...`; zonder `-p` heet het project naar de map, start compose een eigen `db` die op poort 5432 botst en blijft er een volume `<map>_dbdata` achter. Een worktree heeft geen `.env` en geen `secrets/`: maak `secrets/` voor een proef met `draai.sh` vooraf aan en verwijder hem na de laatste run, als los commando.
- Controleer vóór een opdracht over een schermafbeelding of de afbeelding in `main` het gebrek uit het issue toont; zo niet, zeg welke aanpassing aan het script mag, zoals de hoogte van de uitsnede.
- Bouwen twee agents tegelijk en werken ze hetzelfde document bij (zoals `architectuur.md`), dan kiezen ze hetzelfde nieuwe versienummer; de regie lost dat op bij de rebase van de tweede branch.
- Vervalt een regel, zoek dan ook op de omschrijving van het geweigerde geval zelf (zoals "clubboot op een gewone plaats"), niet alleen op de tekst van de oude melding.

#### Review

- Noem bij een securityreview per bestaande controle die de reviewer moet terugzien de functie of het bestand (bijvoorbeeld stuurtekens in `csvbestand.lees`).
- Noem bij een securityreview of de testbestanden in de diff meegetoetst worden, en zo ja op welk punt.
- Leg bij een nareview de stand van de eerste review vast als ref of patchbestand in de scratchpad, zodat de reviewer met `git diff` alleen de nieuwe wijzigingen ziet.
- Wacht op `draai.sh` met `pgrep -f '^bash tests/e2e/draai.sh'` of op het uitvoerbestand; `pgrep -f tests/e2e/draai.sh` en `'[d]raai.sh'` vinden ook wachtlussen van andere agents.
- Een mutant op een gemounte map draai je met `docker compose ... run -v <kopie>:/app/<map>:ro test pytest ...`, zonder de werkmap te wijzigen. Wis niets in de scratchpad; gebruik voor een nieuwe poging een nieuwe map.
- Draai een mutant op een gedeelde set of functie tegen de hele unitsuite, of noem de test die de set bewaakt (zoals `test_log.py` voor `log.TECHNISCH`).
- Noem in een reviewbrief voor aegis de securityrelevante paden apart van schermafbeeldingen en CSS, en noem per nieuw sjabloon of nieuwe macro op welke pagina's die wordt ingevoegd.
- Vraagt een criterium "geen ERROR-regel in de log", zeg dan of een test met `caplog` verwacht wordt of dat een 200 met melding als statisch bewijs volstaat.
- Laat bij een invoercontrole vóór een databasekolom de reviewer de door Python genormaliseerde vormen met een leesquery naar het kolomtype casten (`SELECT '<waarde>'::<type>`), via stdin.
- Draaien twee reviewers tegelijk en start één een proef met containers, zeg dan of de ander daarin met `docker exec` mag lezen (met de projectnaam), of statisch blijft.
- Stelt een brief de reviewer een vraag (zoals "komt een oud-lid erdoor?"), noem dan de test die het bewijst, of zeg dat er geen test is.
- Heeft de regie na de bouw iets hersteld, zeg dan in de brief dat de mutanten van de bouwer verouderd zijn, en lever bij een eigen mutant de diff tegen de gestagede bron mee (`git show :<pad> | diff - <mutant>`).
- Stuurt een oude route na de wijziging door naar de nieuwe, toets dan de doorverwijzing zelf (`location` of de JSON-url); een test op de eindpagina slaagt ook via de omweg.
- Zeg per toetspunt in een reviewbrief of het een run vraagt (met het commando) of statisch mag; een E2E-selector die alleen tekst leest, mag statisch als de tekst niet verandert.
- Zeg in een reviewbrief of de unitsuite en de E2E-suite tegelijk mogen draaien. `draai.sh` duurt meer dan tien minuten: start hem in de achtergrond en tel de uitkomst over alle sessies op.
- Toets een opgehaald of gekoppeld bestand ook met de rechten die de beschreven stap oplevert (zoals 0644 na `curl`), en controleer het resultaat in de database, niet alleen de status `healthy`.
- Zeg of een reviewer een los script met de unitfixture mag draaien: die maakt `botenloods_test` opnieuw aan en breekt een run die tegelijk loopt.
- Noem bij een logregel uit een ADR voor welke story hij geldt, en bij een nareview de regel in de ADR die de reviewer moet terugzien.
- Noem in een brief aan een reviewer de niet-gestagede bestanden in de werkmap en of de review ze negeert.
- Noem als voorbeeldtest in een brief alleen een naam die `grep -rn "def test_" tests/` oplevert.
- Citeer een overlayregel in een brief letterlijk, inclusief de afbakening tussen haakjes, en noem welke routes er bewust buiten vallen.
- Beantwoordt het issue een vraag die je aan de reviewer stelt, noem dan de regel uit het issue erbij.
- Geef een reviewer de paden van de ADR's en de verwachte waarden voor drempels (rate limit, vergrendeling, sessieduur), zodat hij toetst tegen een norm.
- Noem bij elke bronsoort die een reviewer laat toetsen het verwachte gedrag (opslaan of afwijzen).
- Noem bij elke review welke regels in de overlay na de bouw zijn toegevoegd; een ontbrekende test op zo'n regel is een restpunt (ernst laag) en blokkeert de review niet.
- Een reviewer controleert vóór een testrun met `git diff --stat` dat de gemounte paden geen niet-gestagede wijzigingen hebben; anders toetst de test niet de gestagede diff.
- Een nieuw Python-bestand buiten `app/` en `tests/` (zoals `docker/`) lint de reviewer met `-v $PWD/<map>:/app/<map>:ro` en `ruff check --no-cache <map>`; de testcontainer mount die map niet.
- Een reviewer die een eigen test draait, mount de scratchpad op `/app/scratch` en draait `pytest -p tests.unit.conftest /app/scratch/<bestand>` met `-e PYTHONPATH=/app`, nooit een bestand onder `tests/`.
- Een eigen proef met `-p tests.unit.conftest /app/scratch/<bestand>` draait los, niet in dezelfde run als een bestand onder `tests/unit/`.
- Een live proef van aegis met een eigen beheerder in `web` vraagt vooraf toestemming in de omgeving. Zonder die toestemming toetst aegis CSRF en autorisatie statisch en meldt dat in het oordeel.
- Een testnaam noemt alleen de routes of schermen die de test opvraagt.
- Draai de unitsuite op een proefimage met `docker compose -f docker-compose.yml -f compose.dev.yml -f <scratchpad>/compose.<proef>.yml --profile test run --rm test pytest -q`; het override-bestand zet alleen `services.test.image: <proefimage>` en `pull_policy: never`. Hertag `botenloods-dev` niet, anderen gebruiken het.
- Ruff draait in de testcontainer met `ruff check --no-cache`. Een lintfout buiten de diff blokkeert de review niet; meld bestand:regel en of er al een issue voor is.
- Een mutant draai je als bind mount over het bestand in de testcontainer (`docker compose ... run --rm -v <scratchpad>/mutant.py:/app/<pad>:ro test pytest ...`), niet in de werkmap; zo raakt hij de draaiende stack niet. Draai hem tegen het hele testbestand van de wijziging, niet met een `-k`-selectie op naam. Lever bij elke mutant het doelpad in de container en het volledige `docker compose ... run --rm -v`-commando in een `commando.txt` naast de mutanten.
- Haalt een mutant een controle met twee kanten weg (zoals een ledenboot op een clubplaats en een boot op een plaats voor een andere bootsoort), draai dan per kant een eigen mutant, met per kant de assert die moet falen.
- Wordt een lus in een Jinja-macro gewijzigd, noem dan elke aanroep van de macro en de mutant die alleen één aanroep raakt.
- Noem bij een test op escaping de mutant met `|safe` op het veld, en of de regie die al heeft gedraaid. Een templatemutant draait als bind mount van alleen het template: `docker compose -f docker-compose.yml -f compose.dev.yml run --rm -v <scratchpad>/<template>.html:/app/app/web/templates/<template>.html:ro test pytest -q <testbestand>`.
- Een mutant die een object uit `upgrade()` weghaalt, haalt de bijbehorende regel uit `downgrade()` ook weg; anders faalt de mutant op de downgrade in plaats van op de assert van het criterium.
- Controleer een mutant in een bestand dat al gestaged is met `cmp` tegen een kopie, niet met `git diff`; een mutant die de gestagede versie terugzet, is in `git diff` onzichtbaar.
- Een mutant op een staatsassert verandert de code onder test zo dat de redirect blijft en het effect toch plaatsvindt; noem in de brief het bestand van die code.
- Noem per mutant de assert van het criterium waarop hij moet falen, als bestand:regel en niet als omschrijving; een mutant die op een andere assert faalt, bewijst dat criterium niet.
- Een mutant telt pas als gevangen wanneer de reviewer de falende assert noemt, niet alleen het aantal mislukte tests. Meldt een agent dat een mutant overleeft, dan noemt hij de exacte diff van die mutant en het commando, zodat de reviewer hetzelfde kan draaien.
- Draait sentinel parallel op dezelfde database, zeg dan wie de mutanten draait; aegis draait dan geen suite en geen `draai.sh`.
- Een test die een mutant moet vangen, faalt op een assert met een eigen melding; een databasefout als faalreden noemt de reviewer apart.
- Wijzigt een diff meer dan één controle, dan draait de reviewer per controle een aparte mutant en noemt per mutant de test die valt. Levert de regie mutanten aan, dan ook per controle, met de verwachte falende assert als bestand:regel.
- Kiest de bouw een andere oplossing dan de actie in het issue, werk dan het issue bij vóór de review.
- Na een update van het lockbestand controleert de reviewer met een versiecheck in de testcontainer dat de suite tegen de nieuwe versies draait, voordat hij het aantal geslaagde tests meldt.
- Filter de uitvoer van een mutantrun op `^E |FAILED|passed|failed`; de laatste regel kan een logregel van de app zijn.
- Toets een foutafhandeling van de API ook op een onbekend pad en een verkeerde methode onder `/api/v1/`; een `bp.errorhandler` dekt die niet, een `bp.app_errorhandler` wel.
- Noem in een reviewbrief naast het E2E-bestand van het scherm ook de E2E-test die het geweigerde pad bewijst, met de naam voor `draai.sh -k`.
- Raken meer pull requests hetzelfde bestand, laat de reviewer ze dan in een eigen clone proefmergen in de voorgestelde volgorde en melden welke een rebase nodig heeft; `mergeable` van GitHub geldt per pull request, niet voor de reeks.
- Een pull request dat een bestand in `.github/workflows/` wijzigt, mergt alleen met een `gh`-token met de scope `workflow`; zonder die scope weigert GitHub de merge.
- Noem bij een vraag over meer HTTP-methoden of statussen of de test per methode of status moet bestaan, of dat één codepad dat er geen onderscheid in maakt volstaat.
- Zeg in een reviewbrief of een risico dat al op een ander pad in dezelfde functie bestaat (zoals een onbegrensde `read()`) als bevinding telt of als adviespunt.
- Noem de Python-versie van de container (3.14) in de brief, zodat de reviewer niet hoeft na te gaan wat de standaardbibliotheek afhandelt.
- Noem bij een review van een basisimage dat `.github/workflows/images.yml` alleen `linux/amd64` bouwt, zodat de reviewer weet welke architectuur de scan moet dekken.
- Noem bij een test op een HTTP-antwoord welke vormen hij dekt (met `Content-Length`, chunked, zonder lengte), zodat de reviewer alleen de rest hoeft na te gaan.
- Zeg in de brief: draai elke testrun of mutant als een los commando, geen lussen of ketens in één shellregel.
- Noem bij een gewijzigde gedeelde functie de andere aanroepers, of vraag de reviewer die na te lopen.
- Noem bij een mutant op een controle in de route of het template dezelfde controle ook doet; is dat zo, lever dan een gecombineerde mutant op route en template, met de assert die moet falen.
- Noem bij `draai.sh -k` een deel van de testnaam, niet de uitnodigingssoort, en controleer de selectie met `--collect-only`.
- Een mutant op `tests/proxy/klant.py` of `tests/proxy/compose.traefik.yml` draait in een kopie met `docker-compose.yml`, `compose.api-extern.yml`, `docker/db-init.sh`, een leeg bestand `secrets/api_token` en `tests/proxy/`, alles uit de index (`git show :pad`).
- Een mutant op een controlefunctie in `tests/proxy/klant.py` draai je samen met een mutant op de labels die een antwoord van de applicatie oplevert; anders kan de mutant tegen een echte Traefik niet falen. Opruimen en controleren zijn aparte commando's.
- Noem bij een configwijziging welke diensten (web, api, worker) de instelling lezen, zodat de reviewer niet hoeft te zoeken of een andere dienst geraakt wordt.
- Een reviewer van de API proeft via Traefik vanaf het netwerk `koppeling` op `10.203.0.2:8081`, niet via `127.0.0.1:8080`: daar is geen router voor `/api/`. Traefik weigert `%2F`, `%5C`, `%25` en `%00` in het pad zelf (lege 400, `compose.dev.yml`); noem in de brief welke weigering van Traefik komt en welke van de applicatie.
- Vraag je of een proefscript moet veranderen, noem dan de functies die de geraakte status beoordelen (zoals `status()` en `iprem()` in `tests/proxy/klant.py`) en welke bron daar als goed telt.
- Reviewen twee agents tegelijk en draait er één de suite, geef de ander dan voor zijn eigen proef met de fixtures een eigen `TEST_DB` (regel in Bouw); ook een losse proef op `botenloods_test` verstoort de suite. Maak die database met een kopie van `tests/unit/conftest.py` waarin alleen `TEST_DB` anders is, gemount over `/app/tests/unit/conftest.py`; een conftest die `TEST_DB` na de import overschrijft, verandert de URL's niet. De proefmap op `/app/scratch` krijgt daarnaast een `conftest.py` met `from tests.unit.conftest import *`.
- Loopt een filter meer wegen af naar dezelfde gegevens (zoals `__cause__` en `.orig`), maak dan per weg een mutant en noem welke test die weg dekt.
- Noemt een regel in de overlay een tabel, kolom of constraint, toets die dan tegen `app/models.py`.
- Noem een mutant alleen met een code die in de specificatiebestanden van de bouwer staat; staat hij er niet in, noem dan de vervangtekst.
- Noem bij een mutant de nieuwe assert die hem moet vangen (bestand:regel), en zeg erbij als een bredere assert hem eerder vangt.
- Moet de reviewer een mutant tegen de E2E-stack draaien, zeg dan of `web` daarvoor even met een kopie mag draaien. Anders volstaat bewijs uit de data van de seed, zoals een leesquery die laat zien dat de seed het geval bevat.
- Vraag je een reviewer of gegevens "via een andere weg" binnenkomen, noem dan ook de bronadapter in `integratie/koppeling/` als te toetsen pad, met het filter dat bepaalt wat de bron als lid levert.
- Wijzigt een diff een regel uit een ADR, laat de reviewer dan in alle ADR's en documentatie zoeken naar verwijzingen naar die regel en naar de oude formulering, ook buiten de gestagede bestanden.
- Rekent een migratie met `CURRENT_DATE`, noem dan de tijdzone van de database (`SHOW timezone`, Etc/UTC) en die van de installatie (`TZ`, Europe/Amsterdam).
- Geef bij een nareview de regelnummers van de nieuwe hunks of een diff tussen de eerste en de tweede staging, zodat de reviewer alleen het nieuwe deel leest.
- Noem per mutant uit een testcommentaar de verwachte falende assert als bestand:regel. Een deel van een voorwaarde dat het domein onbereikbaar maakt (zoals `not clubboot` bij een boot op de wachtlijst), noem je als gelijkwaardige mutant die niet gedraaid hoeft te worden.
- Noem bij een controle die alleen voor één soort geldt (zoals robottokens) ook de mutant die de soortvoorwaarde weghaalt, met de test die daarop valt.
- Lint in de testcontainer draai je met `ruff check --no-cache <paden>`; de cache in `/app` is niet beschrijfbaar.

#### E2E

- Een proef op volgorde of volume van het technische log schrijft vooraf minstens 50 regels van een andere actie dan de gezochte, met `log.schrijf` via `docker compose exec web`, niet via de interface; dan blijven er geen beheerders of andere gegevens achter. De oude test moet aantoonbaar falen op die ruis voordat het herstel telt.
- Elke E2E-test draait ook los: `tests/e2e/draai.sh -k <testnaam>`, zonder pad, want de e2e-container werkt vanuit `tests/e2e`. Laat de reviewer één test met `-k` draaien als controle op de volgorde.
- Een E2E-test leunt niet op gegevens van een eerder testbestand. Bestaat er geen route om ze in de test te maken (zoals een token), dan maakt `tests/e2e/draai.sh` ze vers vóór elke aanroep van pytest. Een E2E-test die gedeelde instellingen wijzigt, zet ze ook terug als hij faalt (try/finally), of krijgt een eigen installatie.
- De rate limit op `/inloggen` en `/uitnodiging` telt alle E2E-tests samen; `tests/e2e/draai.sh` draait per bestand met 40 seconden pauze. Houd een nieuw E2E-bestand onder 20 inlogverzoeken. Een nieuwe E2E-test die inlogt, krijgt een eigen soort in de lijst van uitnodigingen in `tests/e2e/draai.sh`, vóór `passkey`.
- `tests/e2e/draai.sh` herstart de integratiecontainer en vervangt `secrets/api_token`; meld dat aan de andere agents als die de stack tegelijk gebruiken. `draai.sh` bouwt niet: wijzigt `tests/e2e/requirements.txt`, herbouw dan eerst het e2e-image (`docker compose -f docker-compose.yml -f compose.dev.yml --profile e2e build e2e`) en controleer de versies met `pip list`.
- Proef een foutpad in een shellscript in elke context waarin het script de functie aanroept: een arraytoewijzing met meer `$(...)` (alleen de laatste telt voor `set -e`), een functie achter `||` of in `if` (daar werkt `set -e` niet), niet alleen de functie los. Proef de versie uit de index (`git show :pad`) in de scratchpad, met een stub voor externe commando's, en vergelijk de uitvoer van een geslaagde run met die van vóór de wijziging.
- Een E2E-mutant op een template draai je met `DRAAI_OVERRIDE=<scratchpad>/compose.<mutant>.yml tests/e2e/draai.sh -k <test>`; de override legt het mutant-template als `:ro` bind mount over `/app/app/web/templates/<naam>.html` van `web`. Zet `web` daarna zonder override terug (`up -d --no-deps --force-recreate web`) en controleer met `docker exec botenloods-web-1 grep -c <sleutel> <pad>` dat het origineel draait. De gedeelde `web` herstart daarvoor twee keer; meld dat.
- Geeft `schermafbeeldingen.sh` een `FileNotFoundError`, draai hem dan met `DOC_UIT=/documentatie/gebruikers/<tijdelijke map>` en kopieer alleen de eigen afbeeldingen.
- Een E2E-mutant op een bestand in `app/web/static/` kan niet als bind mount, want de E2E-run gebruikt de draaiende `web`. Zeg in de opdracht dat het agent het bestand tijdelijk in de werkmap mag legen en daarna met `cmp` herstelt, en dat geen ander agent tegelijk de stack gebruikt.
- Bewerk `tests/e2e/draai.sh` niet terwijl het draait; bash leest het script tijdens de run.
- Een docker-stub voor `tests/e2e/draai.sh` laat `config -q` falen en geeft bij `config` de regel `sourcerange: 192.0.2.0/24`; anders stopt het script vóór de regel die je test.
- Een reviewer schrijft de volledige uitvoer van elke E2E-run naar zijn scratchpad en filtert daarna; een mislukte run zonder uitvoer telt als niet onderzocht. Een E2E-scenario dat een criterium bewijst, draait hij minstens twee keer; een fout die los staat van de diff meldt hij apart, met test en regel.
- Eerdere runs laten rijen achter. Een E2E-test op een gedeelde lijst controleert daarom de volgorde over de hele kolom, niet op de eerste rij. Een nieuwe plaatscode in een E2E-test krijgt een letter die nog niet voorkomt; controleer met `grep -rn 'f"[A-Z]{STEMPEL}"' tests/e2e`.
- Een letter van `reknaam()` mag binnen één test vaker voorkomen (hetzelfde rek), maar niet in twee verschillende tests; controleer met `grep -rn 'reknaam(' tests/e2e`.
- Een E2E-selector op een tabel gebruikt geen `columnheader`; onder 40rem verbergt de CSS de `thead`. In een E2E-test met `page.pdf()` zet je de media terug met `emulate_media(media="no-override")`, niet met `"screen"`, en wacht je na een klik met `page.wait_for_load_state()` voordat je elementen telt.
- Voedt de functie van een mutant ook de keuzelijst of het formulier (zoals `controleer_past` via `past()`), muteer dan alleen de aanroep in de serverroute, één mutant per kant, en noem per mutant de assert die moet falen als bestand:regel.
- Controleer bij een mutant via tekstvervanging met een telling dat de vervangen tekst precies één keer voorkomt; anders raakt de mutant ook andere functies.
- Kies in een test op volgorde gegevens waarbij de bedoelde volgorde (zoals op id) afwijkt van de alfabetische.
- Verplaats je de dekking van een criterium van E2E naar unittests, noem dan per gegeven uit het criterium (zoals tijdstip en aantallen) de assert die het dekt, en draai een mutant die dat gegeven weghaalt.
- Zet een bouwopdracht een blok dicht in een `details`, zoek dan in `tests/e2e/` en `schermafbeeldingen.py` alle `to_be_visible`, `all_inner_texts`, `fill`, `click` en `select_option` op elementen in dat blok. `to_contain_text` en `all_text_contents` werken ook in een dicht blok, de andere niet; open het blok eerst met de summary.
- Een test op een scherm met een eigen zoekveld zoekt de knop Zoeken binnen `main`; de kop heeft ook een knop Zoeken.
- Een subagent wacht op een achtergrondrun met een `until grep -q`-lus op een eindregel in het uitvoerbestand, en telt het E2E-totaal met een script uit de losse `passed`-regels van `draai.sh`.
- Een E2E-assert op een keuzelijst filtert op de eigen plaatscode; de seed heeft ook vrije plaatsen.
- Een nieuwe foutroute in `draai.sh` toetst ook welke toestand het script achterlaat (integratiecontainer gestart, `secrets/api_token`), niet alleen dat het stopt.

#### Migratie en database

- Een leesquery op de testdatabase draait als `psql -U botenloods -d botenloods_test` in de db-container; de rol `postgres` bestaat niet.
- SQL in de db-container gaat via een bestand in de scratchpad, op stdin aan `psql -At`; geen query als argument in de shellregel.
- Na een nieuwe migratie eerst `docker compose -f docker-compose.yml -f compose.dev.yml up --build -d --wait`; de dienst migrate leest de migraties uit het image. Downgrade en upgrade controleer je via `docker compose -f docker-compose.yml -f compose.dev.yml run --rm migrate alembic ...`, databasecontroles in de db-container met `psql -U botenloods -d botenloods`. Controleer na een migratie de rechten in de database.
- Een reviewer die een downgrade draait, doet dat op een eigen database (`nieuwe_database`), of meldt vooraf aan de andere reviewers dat de gedeelde database even op de vorige revisie staat.
- Moet een reviewer het schrijfgedrag van een rijbeleid of recht bevestigen (zoals het wijzigen van de sleutelkolom of `RETURNING`), geef dan een eigen database via `nieuwe_database` vrij voor proeven met `ROLLBACK`, of zeg dat afleiden uit de documentatie volstaat.
- Een leesquery op `information_schema` of de rechten in de gedeelde database mag; proeven die rate limits of vergrendelingen raken niet.
- Wijzig je databaserechten, zoek dan eerst welke tests en seedcode als die rol schrijven, en noem in je antwoord welke tests je hebt aangepast. `flask seed` draait als de worker (`botenloods_taken`); een nieuwe tabel die seed vult, krijgt rechten voor die rol. Noem bij een domeinfunctie die een nieuwe databaserol raakt de test die als die rol draait (marker of fixture), zodat de reviewer de positieve controle niet zelf hoeft te zoeken.
- Voeg je rijen toe aan een tabel met een startlijst uit een migratie (zoals `bootsoort`), zet die lijst dan in `tests/unit/conftest.py` terug na elke test.
- Vraagt een domeinfunctie om `FOR UPDATE`, lever dan een test met twee sessies die de race laat zien, of noteer in het issue waarom die test ontbreekt. De racetest moet falen met een mutant zonder de vergrendeling; overleeft de mutant, meld dan waarom de vergrendeling toch nodig is.
- Elke nieuwe `with_for_update` in een bouw krijgt in dezelfde bouw zijn racetest; de reviewbrief noemt per nieuwe `with_for_update` de racetest of de notitie in het issue.
- Een racetest voor een domeinfunctie laadt het object eerst in dezelfde sessie, zoals `laad_beheerder` dat doet, zodat verouderde attributen na `with_for_update` zichtbaar worden. Gebruik `populate_existing=True` bij een vergrendeling van een object dat al geladen kan zijn. Een racetest via `race()` toetst `populate_existing` niet, omdat de actie in een verse sessie draait; laad het object in de actie eerst zonder slot als dat getoetst moet worden.
- Een racetest die verouderde attributen toetst, houdt het eerst geladen object vast in een variabele tot na de aanroep; anders ruimt de identity map het op en overleeft de mutant zonder `populate_existing`.
- Vergrendelt een domeinfunctie boot en plaats, dan eerst de boot en daarna de plaats, net als `toewijzen` en `boot_wijzigen`; een andere volgorde kan een deadlock geven. Een wijziging in een vergrendelvolgorde krijgt een racetest die faalt met de oude volgorde (bijvoorbeeld met `FOR UPDATE NOWAIT` op de tweede rij).
- Een domeinfunctie die rijen verwijdert op basis van een eerder gelezen lijst van id's, herhaalt de voorwaarde in de `DELETE` of neemt het slot van de taak die die voorwaarde kan wijzigen (zoals de import).
- Laat bij elke bewaartermijn nalopen wat er met kopieën gebeurt: logs, back-ups, een externe bron die opnieuw synchroniseert, en verwijzingen in andere tabellen.
- Trek je een recht in dat alleen via een cascade nodig lijkt, noem dan de test die als de rol de cascade laat lopen, en controleer dat het model geen ORM-relatie zonder `passive_deletes` naar die tabel heeft.
- `FOR UPDATE` en `FOR KEY SHARE` vragen UPDATE-recht; tel dat mee bij het bepalen van de rechten van een rol.
- Geeft een migratie een rol een recht op een nieuwe tabel, noem dan per recht de code die het gebruikt. Een recht dat alleen via een cascade nodig lijkt, is niet nodig: de cascade draait als eigenaar van de tabel.
- Een nieuw `with_for_update(key_share=True)` krijgt een racetest zoals `tests/unit/test_bootsoorten.py:198`, of een notitie in het issue waarom die ontbreekt.
- Controleer de migratiehead met `ScriptDirectory` in de testcontainer; `run migrate` vraagt om akkoord.
- Bij een rechtenwijziging in een migratie noem je in de brief zowel het testbestand van de migratie als dat van de domeinfunctie; de reviewer draait de mutanten tegen beide samen.
- Bij een rechtenwijziging: draai per recht dat de rol houdt een mutant die alleen dat recht intrekt, en noem per mutant de test die valt; een recht zonder vallende test is niet gedekt. Meld de reviewer of de gedeelde database al op de nieuwe migratie staat, zodat hij de live ACL toetst.
- Bij een rechtenwijziging: zoek in alle tests met de marker `worker` (of `api`) naar setup via de domeinlaag in tabellen die de rol straks niet meer mag schrijven (zoals `foto=` of `png()`), en noem ze vooraf in de opdracht.

#### Security en proxy

- Een wijziging in `.github/dependabot.yml` valideert de reviewer met `check-jsonschema --builtin-schema vendor.dependabot` in een venv in zijn scratchpad. Na de merge laat de regie de stakeholder per ecosysteem de eerstvolgende run in Insights, Dependabot nakijken ("Check for updates"). Bij `docker-compose` gaf `directories` een "unknown error" zonder log; gebruik daar één ingang per map (#230).
- Een proef op de socketproxy noemt de bron van de eerdere proef met nummer en plek (slotcommentaar van #230 en #251). Een mutant met schrijfrecht gebruikt een aanroep zonder effect, zoals `POST /containers/<bestaat-niet>/stop`, nooit `POST /containers/create` (#251).
- Een brief voor een update van een afhankelijkheid noemt de bron voor de hashes (de JSON van PyPI) en het exacte testcommando per plek waar de versie staat: `uv.lock`, `integratie/requirements-test.txt` en `tests/e2e/requirements.txt` (#258).
- Wijkt de bouwer af van een ADR op een securitycontrole (sleutel van de rate limit, adres voor de whitelist), dan toont hij met een proef dat de eigenschap uit de ADR blijft gelden; anders legt hij de afwijking vóór de bouw aan foundation voor.
- Komt een handeling die eerst alleen via de CLI kon in de webinterface, noem dat in de brief aan de reviewer. Elke webroute met blijvend effect (een link, een nieuw account, een nieuwe inlogmethode) vraagt een recente inlog (ADR-001).
- Komt er een nieuwe route met querystring of padparameter die persoonsgegevens kan bevatten, controleer dan het maskeren in de toegangslog van Gunicorn (`app/toegangslog.py`).
- Controleer na elke wijziging aan de proxy of de toegangslog dat elk verzoek precies één logregel geeft, in het formaat `zonder_code`, in de log van `web` of `api`, en niets in de log van Traefik. Regels die Traefik zelf logt (zoals een verzoek zonder router) tellen apart; meld of zo'n regel gewenst is.
- Draai na elke nieuwe schrijfroute in de API één aanroep via de proxy tegen de draaiende stack voordat je unittests als bewijs telt; de unittests zetten CSRF en de proxy niet altijd zoals productie.
- Noem de poort van de lokale proxy (`127.0.0.1:8080`, Host `localhost`) in elke brief aan een reviewer die via de proxy controleert. Geef een reviewer van de API een container op het netwerk `koppeling` mee (`docker run --rm -i --network botenloods_koppeling --entrypoint python botenloods-app`), zodat hij whitelist en rate limit positief kan controleren. Geef hem ook een tweede token zonder het recht van de nieuwe route mee (of zeg dat hij er een mag maken), zodat hij de 403 via de proxy kan controleren.
- Moet een reviewer een webroute positief via de proxy toetsen, geef dan een testaccount of een sessiecookie voor de lokale stack mee; anders blijft de controle op de inlogplicht statisch.
- Een proef op een gedeelde rate limit doe je in een losse Traefik met de gestagede labels (eigen teller, stub als upstream); de gedeelde proxy alleen voor proeven onder de grens. Render de labels met `docker compose config` met dummywaarden voor de verplichte variabelen. De stub leest de body en geeft 200. Toetst de proef ook wat de applicatie doet (zoals een omzeilde rate limit), gebruik dan als upstream Flask achter Gunicorn met dezelfde routes, niet alleen de stub.
- Een proef met veel geweigerde aanroepen in een losse Traefik gebruikt een eigen database (`nieuwe_database`) of meldt vooraf dat er regels `api.geweigerd` in het gedeelde log komen.
- Een proef op een rate limit van Traefik probeert ook het pad met `%2F` en andere gecodeerde tekens. Een proef boven de grens van een proxy stuurt alleen de kop met `Content-Length`, niet het hele lichaam.
- Een proef met een losse Traefik op dezelfde host als de gedeelde stack gebruikt routers op een eigen `Host(...)` en toetst met die `Host`-kop; via de socket(proxy) ziet hij ook de labels van `botenloods-*`.
- Een criterium als "Traefik haalt een certificaat op" bewijs je lokaal met Pebble (`ghcr.io/letsencrypt/pebble`, `tlsPort` 443; `caserver` en `LEGO_CA_CERTIFICATES` in een override; Traefik met een netwerkalias voor het domein), niet als restpunt.
- Een proef die laat zien dat Traefik iets weigert, draait ook een mutant zonder de weigerende optie; anders bewijst een 400 niet dat die optie het doet.
- Een proef op routering in Traefik (welke router een pad krijgt) draait na minstens drie herstarts van Traefik; twee routers die hetzelfde pad kunnen raken, krijgen een expliciete `priority`.
- Noem bij een proef op een weigering welke laag de 400 geeft (Traefik of de applicatie) en hoe dat te zien is: een regel in de log van `web` of geen regel. Weigert de lokale Traefik zelf, laat de reviewer de applicatielaag dan direct op Gunicorn in de container proeven.
- Gaat een proxy of netwerk gedeeld worden met andere diensten, zeg dan of `web` en `api` op het gedeelde netwerk mogen; standaard niet.
- Bij een optie of vlag van een externe component komen de namen en de volledige lijst uit de gebruikte versie (binary of `--help`), en de ADR zegt welke opties bewust ontbreken.
- ADR-008 "zonder metadata" betekent zonder EXIF, tekstblokken en ICC-profiel; de test en de reviewer gebruiken een bronbestand met alle drie. Een issue over metadata noemt in de acceptatiecriteria alle drie de soorten (EXIF, tekstblokken, ICC); vul het aan vóór de bouw.
- Een test met een bijzondere bronvorm (zoals een MPO of een tweede beeld) controleert eerst zelf dat de bron die vorm heeft, bijvoorbeeld `Image.open(bron).format == "MPO"`; anders test hij stil een ander geval als de bibliotheek verandert.
- Een securityronde scant met `trivy fs --include-dev-deps`, bouwt de images uit `git archive <commit>` in de scratchpad en zoekt vóór elke nieuwe bevinding in `docs/architecture/adr/` naar een aanvaard restrisico op hetzelfde punt.
- Scan images met `trivy --ignore-unfixed`; meldingen zonder oplossing komen alleen als aantal in het rapport.
- Leg bij een update van het lockbestand eerst de uploaddatum van elke doelversie naast `exclude-newer`. Is een versie jonger dan twee weken, dan wacht de update (ernst laag of middel) of beslist de stakeholder (ernst hoog). Een uitzondering in `exclude-newer-package` krijgt een einddatum in het commentaar en verdwijnt zodra `exclude-newer` die datum passeert.
- Noem bij een wijziging van `.github/dependabot.yml` hoe na de merge wordt gecontroleerd dat elk manifest gevonden is (Insights, Dependency graph, Dependabot), en wie dat doet. Dependabot leest in een Dockerfile alleen `FROM`; een image in `RUN --mount=from=` of `docker run` krijgt geen updates.
- `exclude-newer` in `pyproject.toml` is een vaste datum. Dependabot lockt binnen die grens, dus een voorstel voor uv komt pas nadat de regie de datum ophoogt (#59). Noem bij een supply-chainwijziging hoe `exclude-newer` wordt bijgehouden en of Dependabot daarbinnen nog iets kan voorstellen.
- De release-workflow scant met trivy en pusht alleen het gescande image; een melding critical of high met een oplossing stopt de release (#59).
- Scan vóór het taggen van een release beide images lokaal (amd64) met de Trivy-regel uit `images.yml`. Een melding blokkeert anders pas na het taggen, en dan moet de release opnieuw (#199).
- Het releaseissue noemt per E2E-run vóór de tag de commit en de aantallen geslaagd, mislukt en overgeslagen, ook als de stakeholder de runs draaide. Ontbreken de aantallen, dan zegt het slotcommentaar dat (#257).
- Een melding in een Debian-pakket waarvan de nieuwste digest van het basisimage de fix nog niet heeft, los je op met `apt-get install` van dat pakket in de eindstage, met een `shortcut:`-comment die alle CVE's noemt (#199).
- Gaat een geëscapete zoektekst in SQL nog door een normalisatie (zoals `unaccent`, `lower` of `translate`), controleer dan of die normalisatie `%`, `_` of `\` kan maken, en escape ná de normalisatie (#232, AEG-01).
- Draai `uv lock --check` met `--platform linux/arm64` op `python:3.14-slim` (op de Mac) en lees de exitcode zonder pipe (`; echo exit=$?`).
- Draai na een update van ruff `ruff check --no-cache .` in de testcontainer; nieuwe meldingen los je in dezelfde ronde op.
- Bij een sprong over minorversies van uv legt de reviewer de breaking changes uit de releasenotes naast `uv.lock` (archiefformaten, hashtypen) en naast de Python-versie in `/opt/venv`.
- Is de doelversie van een Dependabot-PR jonger dan de cooldown, neem dan de nieuwste versie die wel oud genoeg is en sluit de PR met een verwijzing naar het issue (#196).
- Controleer bij elke Dependabot-PR de publicatiedatum van de doelversie tegen de cooldown van 14 dagen, en lees de PR-tekst op "Cooldown could not be applied". Voor images uit ghcr.io (zoals uv) werkt de cooldown niet vanzelf.
- Een uitzondering in `exclude-newer-package` noemt één einddatum: de waarde van `exclude-newer` waarbij hij vervalt, geen tweede kalenderdatum.
- Verdwijnt een trivy-melding na een wijziging van versie of architectuur, vergelijk dan de meegeleverde `.libs`-map van de wheel per architectuur (amd64 en arm64). Een verdwenen melding is pas een oplossing als de bibliotheek zelf is vervangen. De release scant alleen amd64; een lokale scan op een Mac scant arm64.
- Een release krijgt een volledige semver-tag (`v0.1.0`, niet `v0.1`); anders levert de metadata-stap van de workflow geen tags.
- `uv` staat niet op de host. Draai `uv lock` in `python:3.14-slim` met het binaire bestand uit het uv-image in de eerste `FROM`-regel van `docker/Dockerfile` (`docker create` en `docker cp`) en de werkmap als volume; noem dat commando in de brief, zodat een reviewer `uv lock --check` kan draaien. Staat de binary al in de scratchpad, noem dan het pad van de map en dat die op `/uvbin` gemount wordt (`/uvbin/uv`).
- Noem bij een proef op een overlayregel over de rate limit welke eigenschap de proef bewijst, als die een andere middleware toetst (zoals de whitelist).
- Noem bij een review op de grens van de API elke router naar de dienst `api`, dus ook `api-extern` uit `compose.api-extern.yml`.
- Noem bij een review van een grens op verzoeken of de dienst ook buiten Traefik bereikbaar is (gepubliceerde poort, gedeeld netwerk), en zo ja via welke route.
- Een proef via de proxy met `http.client` die de Host-kop zelf zet, gebruikt `putrequest(..., skip_host=True)`; anders geeft Traefik 400.
- Een proef met veel verzoeken via Traefik gebruikt per verzoek een eigen Authorization-kop en blijft onder 50 verzoeken per adres; anders meet je de rate limit.
- Bij een update van een afhankelijkheid van webauthn noemt de opdracht of de E2E-test voor passkeys gedraaid is, en welk pad die test niet raakt (attestatie tpm en android-key).
- Een grens die alleen achter Traefik en Gunicorn werkt (buffering, lichaam weglezen), krijgt een E2E-test aan beide kanten van de buitengrens, met de herkomst van elke 413, zoals `tests/e2e/test_import.py` voor de API.
- Een reviewer die een webroute met sessie via de proxy toetst, mag in de container `web` een eigen beheerder `aegis<issue>` aanmaken en een sessiecookie tekenen met `app.session_interface.get_signing_serializer(app)`; hij verwijdert die beheerder daarna met een delete op id én gebruikersnaam en meldt het id.
- Na de eerste echte release controleert de regie met `docker buildx imagetools inspect` of elke verwachte tag bestaat en hetzelfde digest heeft, en zet de uitkomst in het issue.
- ZAP in de netwerkruimte van Traefik draait met `-port 8099` (8080 is daar bezet). Bewaar de scripts van een DAST-ronde zonder geheimen in de scratchpad en noem hun pad in het verslag, zodat de volgende ronde kan hertoetsen zonder opnieuw te bouwen.
- Een DAST-stack draait zonder de mounts van `app/` uit `compose.dev.yml`, of vanuit een eigen worktree van de te testen commit, zodat parallel werk in de werkmap de test niet verandert. Controleer na de eerste minuut van een ingelogde scan in de toegangslog dat de verzoeken ingelogd zijn (200 op een beschermde route), voordat de active scan doorloopt.
- Draai `tests/proxy/draai.sh` na elke wijziging aan de labels van `api`, aan `compose.api-extern.yml` of aan de eisen aan Traefik; herbouw eerst `botenloods-app` als `app/` gewijzigd is, want het script bouwt niet. Schrijf de uitvoer naar een bestand met tijdstempel en controleer daarna met `docker ps -a` en `docker network ls` dat niets met `proxytest` achterblijft. Een mutant op die labels draai je met `EXTERN_BESTAND=<kopie in de scratchpad>`. Het script draait niet twee keer tegelijk (vaste projectnaam) en toetst het gedrag, niet elke vlag van Traefik: zonder `insecure` of met `forwardedHeaders.trustedIPs` blijft het groen. De tweede ronde toetst het PROXY protocol (`proxyprotocol.trustedips`) op `websecure`, niet op `web`.
- Een proef boven een rate limit van Traefik met TLS stuurt de aanroepen over één keep-alive-verbinding, of controleert dat ze sneller komen dan de grens bijvult; een nieuwe TLS-verbinding per aanroep kost ongeveer 100 ms.
- Een controle op een eigen teller per adres stuurt vanaf het tweede adres minstens drie aanroepen over één keep-alive-verbinding direct na de 429 van het eerste, en verwacht ze alle drie onder de grens; één aanroep kan een bijgevulde plek van een gedeelde teller krijgen.
- Beschrijft de documentatie een vertrouwensinstelling (`trustedips`, een whitelist), noem dan in de brief welke voorwaarde aan de andere kant moet gelden (zoals: de load balancer zet op elke verbinding zelf een PROXY-kop), en laat de reviewer toetsen of de documentatie die voorwaarde noemt.
- Een controle in `draai.sh` die een tweede container start, eist dat die container gestart is en met 0 eindigt; een lege uitkomst van `docker wait` telt als fout. Proef dat met een docker-stub waarin `run -d` faalt. Een herstel van een controle komt met een stub die de oude en de nieuwe conditie draait, met per geval de verwachte uitkomst.
- Noem bij een autorisatiecontrole op `actor.soort` alle aanroepers van de functie en waar hun actor wordt gemaakt (bestand:regel).
- Zet een wijziging meer in de applicatielog (zoals een traceback), dan toetst de test de JSON-logregel na een fout van de database zelf (NOT NULL of UNIQUE op `lid`) met de rol `api` en met een regelovergang in een veldwaarde, en met een fout die de oorspronkelijke tekst zonder keten overneemt (zoals `PendingRollbackError`); `hide_parameters` verbergt de DETAIL van PostgreSQL niet. Een foutmelding in de code bevat geen veldwaarden.
- Bij een nieuwe GET-parameter: de toegangslog (`app/toegangslog.py`) laat de querystring weg en `app/__init__.py` weigert een NUL-teken centraal. De reviewer controleert alleen of de nieuwe route daar niet omheen gaat.
- Noem bij een whitelist- of adrescontrole in welke vorm het clientadres binnenkomt (IPv4 als gewone notatie of als `::ffff:`), of zeg dat het onbekend is.

#### Documentatie, backlog en ADR's

- Of een instelling in de applicatie (door de beheerder) of in de installatie (omgeving) staat, beslist foundation per instelling in een ADR.
- Laat foundation bij een besluit dat een ontwerpdetail openlaat de veiligste eenvoudige variant kiezen en die melden. Nieuwe omgevingsvariabelen en afhankelijkheden die een besluit nodig maakt, mag foundation toevoegen en moet hij melden.
- Raakt een besluit van de stakeholder ook de overlay, dan noemt foundation de verouderde regels in de overlay; de regie werkt ze bij.
- Laat apex elk acceptatiecriterium toetsen aan de besluiten in de intake; een criterium dat een besluit tegenspreekt, gaat terug als vraag. Na een besluit van foundation: voeg voor elk besluit een acceptatiecriterium toe aan de story, of meld waarom niet.
- Een uitzondering op een besluit van de stakeholder komt ook in het acceptatiecriterium van de backlog, niet alleen in de ADR. Loop na een besluitcommit elk criterium in de backlog na tegen de ADR-zin over hetzelfde onderwerp.
- Noem bij elk verschoven criterium ook de criteria die van dezelfde latere story afhangen. Noem bij een story die een aanroep uit een latere slice beschrijft (zoals BLB-040 en de bootaantallen) of die aanroep in deze slice gebouwd wordt.
- Een criterium noemt alleen schermen die het gegeven echt tonen; controleer dat vóór de bouw (kaartjes en `/p/` tonen geen bootsoort).
- Verandert een story welke regels een scherm toont, noem dan ook de ADR's die het tonen beschrijven (zoals ADR-002 en ADR-006), zodat het agent ze in dezelfde ronde bijwerkt of er vooraf een issue voor is. Verandert een wijziging wanneer een API-route een foutcode geeft, noem dan ook de documentatie en de OpenAPI-beschrijving van die route, zodat bouwer en reviewer ze in dezelfde ronde bijwerken.
- Tel een nieuw ADR met `wc -w` vóór de oplevering en houd 10 procent marge onder het budget.
- Een woordbudget voor een ADR telt alleen ADR-tekst. Noem per besluitpunt of een korte zin volstaat; bij meer dan vier besluitpunten krijgt het budget 75 woorden per punt.
- Heeft een document nog geen versie of wijzigingslog, begin dan op v1.0.0 en voeg onderaan een wijzigingslog toe. De backlog heeft een wijzigingslog in §9: bij een nieuwe versie komt er een logregel bij en gaat de datum mee.
- Elke slice werkt `documentatie/` bij (handleiding, beheerdocumentatie, screenshots waar een scherm verandert); de reviewer controleert dat. Voorbeeldbestanden in `documentatie/` (zoals `voorbeelden/traefik/compose.yml`) mag een agent bijwerken als een ADR verandert; ze gaan wel langs de review vóór de commit.
- `documentatie/gebruikers/schermafbeeldingen.sh` maakt alle afbeeldingen opnieuw; zet afbeeldingen van schermen die niet veranderd zijn terug met `git checkout`. Een nieuw menu-item verandert alle schermafbeeldingen met de kopbalk; die blijven dan staan en worden niet teruggezet.
- Schermafbeeldingen tonen het testlogo (`tests/fixtures/logo.png`, door `schermafbeeldingen.py` geüpload op Instellingen na het inloggen); de reviewer vergelijkt de kopbalk van één afbeelding met de versie in `HEAD`. Werk niet met twee agents tegelijk in `documentatie/gebruikers/afbeeldingen/` en draai tijdens het script geen checkout of stash. Geeft het script een `FileNotFoundError` op de mount, draai het opnieuw en meld een oorzaak pas als die bewezen is.
- Screenshots en andere opnamen komen uit een eigen stack met een lege, geseede database, nooit uit de gedeelde lokale stack; het agent kiest een eigen projectnaam en een vrij subnet. Noem bij een review van screenshots welke schermen geheimen of persoonsgegevens kunnen tonen; de reviewer bekijkt die eerst en de rest steekproefsgewijs.
- Zeg bij het opschonen van een tekst of regels korter geformuleerd mogen of alleen samengevoegd, met een doel in woorden (bijvoorbeeld 25 procent korter).

## 5. Projectcontracten

| Contract | Regel | Eigenaar | Controle |
|----------|-------|----------|----------|
| Openbare pagina | Toont per plaats alleen plaatscode, boot, foto van de boot en naam van de eigenaar. Nooit adres, telefoon of e-mail. | apex, aegis | E2E-test als niet-ingelogde gebruiker |
| Mutatielog | Elke mutatie wordt gelogd. Onder een overzicht staan de bootmutaties die erbij horen; het technische log staat onder een eigen menuoptie (BLB-043, ADR-006). | foundation | Unit- en E2E-test per mutatie |
| Bewaartermijn | Gegevens van oud-leden en het mutatielog worden 5 jaar bewaard en daarna verwijderd. | foundation | Test op opschoonroutine |
| Wachtlijst | Per bootsoort, met zichtbare wachttijd. De beheerder kiest de toewijzing; de applicatie wijst niet automatisch toe. | apex | E2E-test |
| Clubplaatsen | Gereserveerde plaatsen voor clubboten zijn niet aan leden toe te wijzen. | apex | Unhappy-flow-test |
| Plaatsnamen | De naam van een plaats is te wijzigen zonder dat toewijzingen of QR-codes breken. | foundation | Test |
| Koppeling ledenbron | De koppeling met e-boekhouden draait in een aparte container die alleen via de API werkt, zodat een andere vereniging de container kan vervangen. Terugschrijven van het aantal boten per type staat achter `BOOTAANTALLEN_SCHRIJVEN`, standaard uit (#178). | foundation | Test met nepbron |

## 6. Architectuur- en beveiligingskaders

| Kader | Reden | Bij twijfel |
|-------|-------|-------------|
| Stack: Python, Flask, Gunicorn, PostgreSQL in docker-compose, achter Traefik (ADR-013) | Standaardregel, intake en besluit stakeholder 2026-10-31 (#29) | foundation |
| Tenancy: één vereniging per installatie, geen tenantlaag en geen tenantadministratie | Besluit stakeholder 2026-10-30 | stakeholder |
| Huisstijl: de Dajaks-basis, alle styling via de tokens ervan. Alleen naam en logo zijn per installatie te kiezen; de kleuren zijn vast. | Besluit stakeholder 2026-10-30, gewijzigd 2026-11-06 (issue #150) | foundation |
| Hosting: eigen docker-compose, geen Hansel. De basis blijft gelden: 12-factor-configuratie, secrets via verwijzing, health endpoints, logs naar stdout, container zonder root, achtergrondwerk (zoals de opschoning) buiten het webproces; imports en exports met andere systemen in de integratiecontainer (ADR-012); een CSV die een beheerder in de webinterface uploadt of downloadt, hoort bij `web` (ADR-014). | Afwijking van de standaardregel, besluit stakeholder 2026-10-30. Reden: elke vereniging draait een eigen kleine installatie. | stakeholder |
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
| v0.5.75 | 2026-11-12 | Twee regels (Security en proxy): proef en mutant op de socketproxy, brief voor een update van een afhankelijkheid; uit de terugblikken van pipeline bij #251 en sentinel bij #258 | Lessen |
| v0.5.74 | 2026-11-12 | Regel over mutantruns (Review) aangevuld: één bestand over het testimage mounten; uit de terugblik van sentinel bij #255 | Lessen |
| v0.5.73 | 2026-11-12 | Eén regel (Security en proxy): aantallen van de E2E-runs in het releaseissue; uit de release van v1.0.2 | Lessen |
| v0.5.72 | 2026-11-12 | Drie regels (Review): verwachte falende assert en gelijkwaardige mutant, mutant op de soortvoorwaarde, ruff zonder cache; één regel (Security en proxy): vorm van het clientadres; uit de terugblikken van sentinel en aegis bij #240, #176, #208 en #243 | Lessen |
| v0.5.71 | 2026-11-12 | Regel over SendMessage aangepast (subagent levert via de hand-back), pad van de handleiding (Algemeen), versmalde weigering (Bouw), bestaande controles in een securitybrief (Review), Dependabot-configuratie (Security en proxy); uit de terugblikken van apex, bedrock, sentinel, aegis en pipeline bij #214, #230, #240 en #176 | Lessen |
| v0.5.70 | 2026-11-11 | Regel over E2E-bestandsnamen tot #213 en de wisselvallige tests #172 en #217 weg (opgelost); één regel (E2E) en één (Review) uit de terugblikken van prism, sentinel en aegis: ruis bij een volgordeproef op het log, testbestanden in een securityreview | Lessen |
| v0.5.69 | 2026-11-11 | Eén regel (Security en proxy) uit de terugblik van probe bij #237: mutant zonder de weigerende optie | Lessen |
| v0.5.68 | 2026-11-11 | §4: `Refs` in plaats van `Closes` bij een criterium dat pas na de merge te toetsen is (#230) | Lessen |
| v0.5.67 | 2026-11-11 | Uit de terugblikken bij #230: eigen `Host` in een losse Traefik, Pebble voor ACME (Security en proxy); lezen in een proef van een andere reviewer (Review) | Lessen |
| v0.5.66 | 2026-11-11 | Twee regels (Review) uit de terugblikken bij #231: bewijs voor "geen ERROR-regel", casten naar het kolomtype | Lessen |
| v0.5.65 | 2026-11-11 | Omvang 11 rekken en 229 plaatsen volgens de echte indeling (§3, Algemeen) | #236 |
| v0.5.64 | 2026-11-11 | Uit de terugblikken bij #234: E2E-mutant op een template, `DOC_UIT` bij een `FileNotFoundError` (E2E); run of statisch per toetspunt (Review) | Lessen |
| v0.5.63 | 2026-11-11 | Uit de terugblikken bij #233: unieke mapnamen voor mutanten, boot van een oud-lid in een test (Bouw); de backlog heeft wel een wijzigingslog (Documentatie) | Lessen |
| v0.5.62 | 2026-11-11 | Uit de terugblikken bij #232: escape na een normalisatie (Security en proxy), geen tekstwijziging tijdens een testrun (Bouw), Python via `web` ook voor reviewers (Bouw), rol voor psql op de testdatabase (Migratie en database) | Lessen |
| v0.5.61 | 2026-11-11 | Twee regels (Security en proxy) uit de terugblik van sentinel bij #235: `uv lock --check` op arm64 met exitcode, ruff na een update | Lessen |
| v0.5.60 | 2026-11-11 | Eén regel (Security en proxy) uit de terugblik van probe bij de DAST vóór v1.0.0 | Lessen |
| v0.5.59 | 2026-11-10 | Eén regel (Security en proxy) uit de terugblik van aegis bij de securityronde vóór v1.0.0 | Lessen |
| v0.5.58 | 2026-11-10 | Twee regels (Security en proxy) uit #196 en de terugblik van sentinel: breuken bij een sprong in uv, versie binnen de cooldown kiezen | Lessen |
| v0.5.57 | 2026-11-10 | Uit de terugblikken bij #221 en #223 en de ervaring van de regie: drie nieuwe regels (Algemeen) over filters op externe invoer, gedeelde functies en berichten naar `main`; één nieuw (Review) over de nareview; de regel over de worktree (Review) aangevuld met env-bestand en `secrets/`; slotcommentaar vóór de merge (§4) | Lessen |
| v0.5.56 | 2026-11-10 | Uit de terugblikken bij #205 en #220: vier nieuwe regels (Bouw), één nieuw (Review), twee nieuw (E2E); Review regel over twee kanten krijgt een voorbeeld dat na #205 klopt; E2E-uitnodigingssoort vóór `passkey` | Lessen |
| v0.5.55 | 2026-11-10 | Werken in milestones die de regie vooraf met de stakeholder afstemt (§4); drie nieuwe regels (Review) uit de terugblikken van aegis en sentinel bij #203: bronadapter als andere weg, oude ADR-formulering buiten de diff, tijdzone bij `CURRENT_DATE` | Besluit stakeholder 2026-11-10 |
| v0.5.54 | 2026-11-10 | Eén regel (Bouw) aangevuld en één nieuw (Bouw), twee nieuw (Review) uit de terugblikken van bedrock, sentinel en aegis bij #202: mutant per voorwaarde, wisselvallige test #217, bewijs bij een vraag aan de reviewer, verouderde mutanten na een herstel | Lessen |
| v0.5.53 | 2026-11-10 | Eén regel (Bouw) aangescherpt en drie nieuw (Bouw), één nieuw (Migratie en database), drie nieuw (Review) uit de terugblikken van bedrock, sentinel en aegis bij #204: volledige unitsuite na een eigen herstel, mutant met python3 en controle, overgenomen bouw, E2E-bestandsnaam tot #213, racetest bij elke nieuwe `with_for_update`, eigen proef los, live proef van aegis, testnaam | Lessen |
| v0.5.52 | 2026-11-10 | Eén regel (Bouw) aangescherpt en drie nieuw (Bouw), twee nieuw (Security en proxy) uit de terugblikken van bedrock, sentinel en aegis bij #190: mutanten altijd op een kopie, blok open na weigering, melding per toestand, eigen testgegevens opruimen, E2E aan beide kanten van een proxygrens, eigen sessie voor de reviewer | Lessen |
| v0.5.51 | 2026-11-10 | Drie regels (Security en proxy) uit release 0.4.0/0.4.1 en de terugblikken van sentinel bij #199 en de Dependabot-PR's: lokaal scannen vóór het taggen, zlib-fix via apt met alle CVE's, cooldown per Dependabot-PR controleren | Lessen |
| v0.5.50 | 2026-11-09 | Twee regels (Bouw) aangevuld en één nieuw (Bouw), één regel (Review) uit de terugblikken van prism en sentinel bij #179: zoeken in `tests/unit/` naar een weggehaalde tekst, mutant bij een E2E-vergelijking, bestaande schermafbeelding, E2E-mutant of bewijs uit de seed | Lessen |
| v0.5.49 | 2026-11-09 | §3 gevoeligheid van gegevens zonder adres, telefoon en e-mail (#180); twee regels (Review) en één regel (Bouw) uit de terugblikken van bedrock en sentinel bij #180 | Besluit stakeholder, lessen |
| v0.5.48 | 2026-11-09 | Twee regels (Review) en vier regels (Bouw) uit de terugblikken van bedrock, sentinel en aegis bij #186 | Lessen |
| v0.5.47 | 2026-11-08 | Twee regels (Review) en twee regels (Bouw) uit de terugblikken van prism, sentinel en aegis bij blok 4 van #150 | Lessen |
| v0.5.46 | 2026-11-08 | Twee regels (Algemeen) en drie regels (Bouw) uit de terugblikken van bedrock, sentinel en aegis bij #178, en één regel (Review): waarden van een extern filter, WSDL vooraf, zoeken in heel `tests/` bij een weggehaald veld, tests met zeep, mutantrun; §5 terugschrijven achter een schakelaar | Lessen, #178 |
| v0.5.45 | 2026-11-08 | Eén regel (Algemeen) uit de terugblik van bedrock bij #178: aanroepen van een gekozen bibliotheek vooraf controleren | Lessen |
| v0.5.44 | 2026-11-08 | Vier regels (Bouw) en één regel (Review) uit de terugblikken van prism en sentinel bij blok 3 deel B van #150: toetsantwoorden testen, `|safe` per tak, `commando.txt` en mutantlus, basislijn meten, valpunt van een mutant | Lessen |
| v0.5.43 | 2026-11-07 | Drie regels (E2E) en één regel (Security) uit de terugblikken van prism, sentinel en aegis bij blok 3 deel A van #150: dichte `details`, knop Zoeken in `main`, wachten op een achtergrondrun, GET-parameters en toegangslog | Lessen |
| v0.5.42 | 2026-11-07 | Twee regels (Bouw) uit de terugblik van prism bij het scherm vrije plaatsen van #150: commando voor de unitsuite en wisselvallige test #172, schermafbeeldingen terugzetten | Lessen |
| v0.5.41 | 2026-11-07 | Twee regels (Bouw) uit de terugblik van prism bij blok 2 van #150: baseline in een worktree of wachten, foto voor een visuele controle | Lessen |
| v0.5.40 | 2026-11-07 | Vijf regels (Bouw) uit de terugblikken van prism en sentinel bij blok 1 van #150: `web` met `compose.dev.yml`, baseline vóór wijzigingen, selectors zoeken, test op CSS-afwijking, vervangen klassen | Lessen |
| v0.5.39 | 2026-11-07 | Regel (Review) uit de terugblik van sentinel bij #156: rechten van een opgehaald bestand, resultaat in de database | Lessen |
| v0.5.38 | 2026-11-07 | Twee regels (Review, Migratie en database) uit de terugblikken van sentinel en aegis bij #158 | Lessen |
| v0.5.37 | 2026-11-07 | Zes regels in de briefingchecklist (Algemeen, Bouw) uit de bouw van #158 en de toets van Design System | Lessen |
| v0.5.36 | 2026-11-06 | Zeven regels in de briefingchecklist (Bouw, Review) uit de terugblikken van bedrock, sentinel en aegis bij #157 | Lessen |
| v0.5.35 | 2026-11-06 | Regels uit de terugblikken van prism en sentinel bij #150 deel 1: afname controleren, structuurselectors, escapingtest, migratieheadtest, wachtlus | Lessen |
| v0.5.34 | 2026-11-06 | §6: imports en exports met andere systemen in de integratiecontainer, CSV via de webinterface in `web` (ADR-014) | Besluit ADR-014 |
| v0.5.33 | 2026-11-06 | Regel uit de terugblik van foundation (ADR-014): ADR bij bestandsnaam noemen | Lessen |
| v0.5.32 | 2026-11-06 | Model en effort per soort agentopdracht, besluit van de stakeholder | Werkwijze |
| v0.5.31 | 2026-11-06 | Regels uit de review van #143: mutant met telling, volgorde los van alfabet | Lessen |
| v0.5.30 | 2026-11-06 | Regel uit de terugblik van sentinel (#144): mutant op de serverroute, één per kant | Lessen |
| v0.5.29 | 2026-11-06 | Regel uit de terugblik van sentinel (#145): unieke reknamen in E2E controleren | Lessen |
| v0.5.28 | 2026-11-06 | Regel uit de terugblik van sentinel (#142): een telling van 0 in het bewijs verklaren | Lessen |
| v0.5.27 | 2026-11-06 | Regel uit de terugblik van sentinel (#130): een reeks statuscodes ook op herkomst toetsen | Lessen |
| v0.5.26 | 2026-11-06 | Vier regels uit de terugblikken van aegis en sentinel (#137): eigen `TEST_DB` voor een proef naast de suite (met kopie van de conftest), mutant per weg van een filter, overlayregel getoetst tegen het model, logtest op een databasefout met de rol `api`, een regelovergang en een fout zonder keten | Lessen |
| v0.5.25 | 2026-11-06 | Twee regels uit de terugblikken van aegis en sentinel (#133): proef op de API via `koppeling`, functies die een status beoordelen bij een vraag over een proefscript | Lessen |
| v0.5.24 | 2026-11-05 | Drie regels uit de terugblikken van sentinel en aegis (#132): aanroepers van een gedeelde functie, gecombineerde mutant op route en template, `draai.sh -k` op de testnaam | Lessen |
| v0.5.23 | 2026-11-05 | Regel over een mutant per kant van een tweezijdige controle, uit de terugblik van sentinel (#131) | Lessen |
| v0.5.22 | 2026-11-05 | Uit #54: tweede ronde van `draai.sh` (PROXY protocol), keep-alive bij een proef op de rate limit, drie aanroepen voor een eigen teller, voorwaarde bij een vertrouwensinstelling | Werkwijze |
| v0.5.21 | 2026-11-05 | Regel uit de terugblik van foundation bij #54: zoek vóór een besluit naar elke geraakte instelling | Werkwijze |
| v0.5.20 | 2026-11-05 | Twee regels uit de terugblikken van sentinel en aegis bij #127: mutant op `klant.py` samen met een labelmutant, en welke eigenschap een proef op de rate limit bewijst | Werkwijze |
| v0.5.19 | 2026-11-05 | Regel over `tests/proxy/draai.sh` na een wijziging aan de proxy (issue #53); woordgrens per alinea, overlayregels per proef en mutanten op `tests/proxy`, uit de terugblikken van pipeline, aegis en sentinel | Werkwijze, lessen |
| v0.5.18 | 2026-11-05 | Regel over het platform bij een review van een basisimage, uit de terugblik van sentinel (issue #124) | Lessen |
| v0.5.17 | 2026-11-05 | Regel over `uv lock` verwijst naar de uv-stage in `docker/Dockerfile` in plaats van een vaste versie; regel over de unitsuite op een proefimage, uit de terugblik van sentinel (issue #105) | Werkwijze, lessen |
| v0.5.16 | 2026-11-05 | Regels over zoeken in issues op een versienummer en over voorbeeldtests in een brief, uit de terugblik van sentinel (issue #120) | Lessen |
| v0.5.15 | 2026-11-05 | Issue per open Dependabot-PR; mutanten van de regie per controle; issue bijwerken als de bouw afwijkt, uit de terugblikken van sentinel en aegis (issue #118) | Besluit stakeholder 2026-11-05, lessen |
| v0.5.14 | 2026-11-05 | Regels over een mutant per gewijzigde controle en over de aanroepers bij een controle op `actor.soort`, uit de terugblikken van sentinel en aegis (issue #55) | Lessen |
| v0.5.13 | 2026-11-05 | Regels over de vormen van een HTTP-antwoord in een test en losse testcommando's, uit de terugblikken van aegis en sentinel (issue #109) | Lessen |
| v0.5.12 | 2026-11-05 | Regel over letters van `reknaam()` per test, uit de terugblik van sentinel (issue #112) | Lessen |
| v0.5.11 | 2026-11-05 | Regel over de diensten die een instelling lezen, uit de terugblik van sentinel (issue #114) | Lessen |
| v0.5.10 | 2026-11-05 | Regel over mutanten op een Jinja-macro met meer aanroepen, uit de terugblik van sentinel (issue #110) | Lessen |
| v0.5.9 | 2026-11-05 | Regel over een oud image na een nieuwe imagenaam, uit de terugblik van sentinel (issue #34) | Lessen |
| v0.5.8 | 2026-11-05 | Mutant met bestand:regel van de assert; bestaand risico op een ander pad als bevinding of advies, uit de terugblikken van sentinel en aegis (issue #31) | Lessen |
| v0.5.7 | 2026-11-05 | Regel over de controle van Dependabot na de merge, uit de terugblik van sentinel (issue #25) | Lessen |
| v0.5.6 | 2026-11-05 | Regels over een mutant op `upgrade()` en over schrijfproeven op een rijbeleid, uit de terugblikken van sentinel en aegis (issue #24) | Lessen |
| v0.5.5 | 2026-11-05 | Regels over tests per HTTP-methode of status en over de Python-versie in de brief, uit de terugblikken van aegis en sentinel (issue #23) | Lessen |
| v0.5.4 | 2026-11-05 | Regels over het citeren van een overlayregel en over een mutant op een staatsassert, uit de terugblikken van aegis en sentinel (issue #12) | Lessen |
| v0.5.3 | 2026-11-05 | Regels over de assert per mutant en over een E2E-mutant op een static-bestand, uit de terugblikken van prism en sentinel (issue #99) | Lessen |
| v0.5.2 | 2026-11-05 | Regel over een templatemutant als bind mount van alleen het template, uit de terugblik van sentinel (issue #95) | Lessen |
| v0.5.1 | 2026-11-05 | Vijf regels uit de terugblikken van bedrock, sentinel en pipeline (issues #94 en #96): mutant bij een E2E-assertie, volle suite bij een nieuwe validatieregel, E2E-test van het geweigerde pad, proefmerge van een reeks pull requests, `workflow`-scope | Lessen |
| v0.5.0 | 2026-11-05 | Werkwijze met een branch per feature en een pull request naar `main`, dat de sessie na review zelf mergt | Besluit stakeholder |
| v0.4.26 | 2026-11-04 | Regel over een docker-stub voor `draai.sh`, uit de terugblik van sentinel (issue #92) | Lessen |
| v0.4.25 | 2026-11-04 | Vijf regels uit de terugblikken van sentinel en aegis (issue #91): foutafhandeling op paden zonder view, elke router naar `api`, bereikbaarheid buiten Traefik, eigen token per verzoek en `skip_host` bij een proef via Traefik | Lessen |
| v0.4.24 | 2026-11-04 | Omweg voor `draai.sh` in het nachtvenster vervalt: het script vraagt zelf een import aan (#45); regel over E2E-uitvoer en herhaalde runs uit de terugblik van sentinel | Bouw #45 |
| v0.4.23 | 2026-11-04 | Regel over de `\|safe`-mutant bij een escapingtest, uit de terugblik van sentinel (issues #88 en #89) | Lessen |
| v0.4.21 | 2026-11-04 | Regel over andere schermen met hetzelfde gegeven, uit de terugblik van sentinel (volgorde verdiepingen) | Lessen |
| v0.4.20 | 2026-11-04 | Twee regels uit de terugblik van prism en twee uit die van sentinel (issue #87): afwerklijst bij een nieuwe webroute, volgorde van `Plaats.bootsoorten`, lint buiten `app/` en `tests/`, eigen tests van een reviewer | Lessen |
| v0.4.19 | 2026-11-04 | Regel over een vervangen pakket in status en issues uit de terugblik van sentinel (#86) | Lessen |
| v0.4.18 | 2026-11-04 | Regel over een versiecheck na een lockupdate, uit de terugblik van sentinel; pad van de uv-binary in de brief, uit de terugblik van aegis (issue #63) | Lessen |
| v0.4.17 | 2026-11-04 | Regel over het controleren van de bronvorm in een test, uit de terugblikken van aegis en sentinel; regel over niet-gestagede bestanden in een reviewbrief, uit de herreview van sentinel (issue #70) | Lessen |
| v0.4.16 | 2026-11-04 | Regel over sorteersleutels in een volgordetest, uit de terugblik van sentinel (issue #81) | Lessen |
| v0.4.15 | 2026-11-04 | Regel over het intrekken van een recht naast een cascade, uit de terugblik van aegis; regel over mutanten bij een rechtenwijziging, uit de terugblik van sentinel (issue #85) | Lessen |
| v0.4.14 | 2026-11-04 | Twee regels in de briefingchecklist (Review) uit de terugblik van sentinel (issue #84) | Lessen |
| v0.4.13 | 2026-11-04 | Zes regels in de briefingchecklist (Algemeen, Bouw, Migratie en database) uit de terugblikken van bedrock, aegis en sentinel (issue #83) | Lessen |
| v0.4.12 | 2026-11-04 | Regel voor het woordbudget van een ADR, uit de terugblik van foundation (issue #83) | Lessen |
| v0.4.11 | 2026-11-04 | Regel voor een ontbrekend wijzigingslog, uit de terugblik van apex (issue #82) | Lessen |
| v0.4.10 | 2026-11-04 | Zeven regels in de briefingchecklist en de omweg voor #45 als commando, uit de terugblikken van slice 12 (forge, bedrock, prism, sentinel, aegis) | Lessen |
| v0.4.9 | 2026-11-03 | Besluiten per ronde benoemen; ongecommitte bestanden met een oud besluit noemen | Terugblikken apex en foundation (#80, tweede ronde) |
| v0.4.8 | 2026-11-03 | Woordbudget tellen met een word-diff | Terugblikken apex en foundation (#80) |
| v0.4.7 | 2026-11-03 | Einddatum van een uitzondering, trivy per architectuur, semver-tag, uv via Docker, passkeytest bij webauthn | Terugblikken sentinel en aegis (release v0.1.0, #63) |
| v0.4.6 | 2026-11-03 | Foutpad in een shellscript per aanroepcontext proeven; draai.sh niet bewerken tijdens een run | Terugblik sentinel (#40) |
| v0.4.5 | 2026-11-03 | Afwijking van een acceptatiecriterium vóór de review in het issue; mutant per vervangen aanroep; geen bewerking tijdens een logcontrole | Terugblikken sentinel en aegis (#73, #74) |
| v0.4.4 | 2026-11-03 | Mutant per behouden recht; live ACL melden | Terugblikken sentinel en aegis (#60) |
| v0.4.3 | 2026-11-03 | Rechten van een rol: UPDATE voor vergrendelingen, tests met marker nalopen | Terugblik bedrock (#60) |
| v0.4.2 | 2026-11-03 | Controle van de tags na de eerste release | Terugblik aegis, herstel CI (#59) |
| v0.4.1 | 2026-11-03 | Regels over `exclude-newer` met Dependabot, de trivy-stap in de release en het opschonen van teksten | Review aegis (#59), terugblik #71 |
| v0.4.0 | 2026-11-03 | Briefingchecklist opgeschoond: 137 regels samengevoegd tot 91 en gegroepeerd per soort opdracht (algemeen, bouw, review, E2E, migratie en database, security en proxy, documentatie); geen inhoud vervallen (#71) | Retrospective mijlpaal slice 1 tot en met 11 |
| v0.3.23 | 2026-11-03 | Regels over de laag van een weigering in een proef en over opties van externe componenten, uit de terugblikken van bedrock, aegis en sentinel (#65) | Lessen |
| v0.3.22 | 2026-11-03 | Regel over Flask als upstream in een Traefik-proef, uit de terugblik van foundation (#65) | Lessen |
| v0.3.21 | 2026-11-03 | Negen regels over lockbestand, e2e-image, invoerformaten, metadata en DAST, uit de terugblikken van bedrock (#58), de reviews van #58 en #66 en probe (securityronde na slice 11) | Lessen |
| v0.3.20 | 2026-11-03 | Twee regels over leesquery's en trivy, uit de terugblik van aegis (securityronde na slice 11) | Lessen |
| v0.3.19 | 2026-11-03 | Regels over startlijsten in tests en schermen in criteria, uit de bouw en review van slice 11 (#56); stand | Lessen |
| v0.3.18 | 2026-11-03 | Regels over compose-controles op de host, gereviewde paden en mutanten bij parallelle reviews, uit de reviews van #52 | Lessen |
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
