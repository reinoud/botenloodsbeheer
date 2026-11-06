# Handleiding voor beheerders van de botenloods

Met botenloodsbeheer houd je bij welke boot op welke plaats in de loods ligt en van wie die is. Deze handleiding beschrijft per taak wat je kunt doen en hoe. Ze geldt voor een loods van ongeveer 10 rekken, 160 plaatsen, 210 leden en 180 boten, met 3 beheerders die dezelfde rechten hebben. Er is geen aparte systeembeheerder in de applicatie.

Alle schermen werken in een gewone browser, ook op een telefoon. Schermen over boten en plaatsen tonen onderaan de bootmutaties die erbij horen. De voorbeelden en afbeeldingen gebruiken verzonnen gegevens.

## Inloggen

Je logt in met een passkey (telefoon, vingerafdruk of beveiligingssleutel) of met een wachtwoord plus een code uit een authenticator-app. Een passkey is het eenvoudigst en niet te phishen.

1. Open `/inloggen`.
2. Kies **Inloggen met passkey** en volg de vraag van je apparaat. Of vul je gebruikersnaam en wachtwoord in en kies **Verder**.
3. Bij een wachtwoord vraagt de applicatie daarna de code van zes cijfers uit je authenticator-app.

![Het inlogscherm met een knop voor de passkey en een formulier voor gebruikersnaam en wachtwoord.](afbeeldingen/inloggen.png)

![Het scherm waar je de code van zes cijfers uit je authenticator-app invult.](afbeeldingen/code.png)

Na vijf mislukte pogingen kun je 15 minuten niet met je wachtwoord inloggen. Met een passkey lukt het wel. De applicatie zegt niet of de gebruikersnaam of het wachtwoord fout was. Een sessie duurt 12 uur. Met **Uitloggen** in de menubalk sluit je hem eerder af.

Een paar handelingen vragen een inlog van hooguit 10 minuten oud: een beheerder uitnodigen, herstellen, blokkeren, deblokkeren of verwijderen, inlogmethodes wijzigen en de instellingen opslaan. Is je inlog ouder, dan vraagt de applicatie je opnieuw in te loggen.

## Beheerders

Het scherm `/beheerders` toont alle accounts met hun status en inlogmethodes. De eerste beheerder maakt wie de installatie beheert (zie de beheerdocumentatie). Daarna nodigen jullie elkaar uit.

![De pagina Beheerders met het formulier om uit te nodigen en de lijst met accounts.](afbeeldingen/beheerders.png)

### Een beheerder uitnodigen

1. Vul onder **Beheerder uitnodigen** een gebruikersnaam in (2 tot 50 tekens: a-z, cijfers, punt, streepje en onderstreping) en kies **Uitnodigen**.
2. Geef de link die verschijnt aan de nieuwe beheerder. De link werkt één keer en is 24 uur geldig. Hij staat alleen op dit scherm.
3. De nieuwe beheerder opent de link en kiest een passkey, of een wachtwoord van 12 tot 128 tekens met de QR-code of sleutel voor de authenticator-app en een eerste code.

![Het scherm Beheerder uitgenodigd met de uitnodigingslink, hier onherkenbaar gemaakt.](afbeeldingen/uitnodiging-link.png)

![Het scherm Account instellen met keuze tussen passkey en wachtwoord met authenticator-app.](afbeeldingen/uitnodiging.png)

### Een collega blokkeren, herstellen of verwijderen

Achter elk ander account staan drie knoppen. Je eigen account kun je hier niet wijzigen, zodat er altijd een actieve beheerder blijft.

| Knop | Gevolg |
|---|---|
| Blokkeren | De beheerder kan niet meer inloggen. **Deblokkeren** maakt dat ongedaan. |
| Toegang herstellen | Oude inlogmethodes en sessies vervallen. Je krijgt een nieuwe link van 24 uur voor de collega, bijvoorbeeld na een verloren telefoon. |
| Verwijderen | Het account verdwijnt, met de persoonlijke tokens van die beheerder. Het log blijft. |

### Je eigen inlogmethodes

Op `/profiel` voeg je een passkey of (als je er nog geen hebt) een wachtwoord met authenticator-app toe, of trek je een methode in. Intrekken beëindigt al je sessies. Je houdt altijd minstens één methode.

![Het profiel met de lijst van inlogmethodes en de knop om een passkey toe te voegen.](afbeeldingen/profiel.png)

## Rekken en plaatsen

De loods is ingedeeld in rekken. Een rek heeft een korte naam, een omschrijving en vakken op 1 tot en met 5 verdiepingen, met per verdieping 1 tot en met 12 vakken. Elk vak dat aan staat is een plaats. De aanduiding van een plaats volgt uit rek, verdieping en vak: `A/1/1` is rek A, verdieping 1, vak 1. Een verdieping heeft geen gaten: de vakken zijn altijd 1 tot en met n. Een verdieping met alleen vak 1 en 3 weigert de applicatie, met een melding die de verdieping en het ontbrekende vak noemt.

De pagina `/indeling` toont elk rek met zijn omschrijving en plaatsen. Per plaats staan de aanduiding, de status (vrij, bezet of clubplaats), de boot, de eigenaar en de bootsoorten waarvoor de plaats geschikt is. Een clubplaats is alleen voor boten van de vereniging. Kies een aanduiding om de plaats te openen.

![De pagina Indeling met het formulier voor een nieuw rek, met het raster van verdiepingen en vakken, en het eerste rek.](afbeeldingen/indeling.png)

- **Rek aanmaken:** vul bovenaan een naam in (1 tot 10 tekens, zonder `/`, uniek zonder verschil in hoofdletters) en eventueel een omschrijving (hooguit 60 tekens). Vink in het raster de vakken aan die bestaan. Het raster staat zoals het rek in de loods: verdieping 1 onderaan. Elk vakje heet "Verdieping 2, vak 3" voor schermlezers. Kies eventueel per verdieping een bootsoort: elke plaats op die verdieping krijgt die soort als geschikte bootsoort. Een verdieping zonder keuze geeft haar plaatsen geen bootsoort. Kies **Rek aanmaken**.
- **Naam en omschrijving wijzigen:** open **Rek wijzigen of verwijderen**, pas ze aan en kies **Rek opslaan**. Een nieuwe naam verandert de aanduiding van alle plaatsen in het rek. De QR-codes en de toewijzingen blijven gelijk.
- **Vakken aan- of uitzetten:** open **Rek wijzigen of verwijderen**, verander het raster en kies **Indeling opslaan**. Een nieuw vak is een nieuwe plaats, met de bootsoort die je bij Nieuw rek voor die verdieping koos (geen keuze betekent geen bootsoort). Bestaande plaatsen veranderen niet. Een vak dat uit gaat, verdwijnt met zijn plaats. Ligt er een boot op, dan weigert de applicatie en verandert er niets; geef de plaats eerst vrij. Zet je een vak uit dat niet het laatste van zijn verdieping is, dan weigert de applicatie ook, omdat er dan een gat ontstaat. De andere vakken houden hun nummer, boot en QR-code.
- **Rek verwijderen:** kies **Rek ... verwijderen**. Dat lukt alleen als er geen boten meer op liggen.
- **Plaats wijzigen:** open de plaats via de aanduiding. Onder **Plaats wijzigen** pas je bootsoorten en clubstatus aan. De aanduiding zelf wijzigt alleen met de naam van het rek. Een nieuwe plaats heeft de bootsoort van haar verdieping als je die bij Nieuw rek koos; anders vink je er minstens één aan voordat je een boot toewijst. Een plaats weghalen doe je in het raster: zet het vak uit (zie Vakken aan- of uitzetten). Een wijziging die niet past bij de boot die er ligt, weigert de applicatie.

![Het uitgeklapte blok om de naam, omschrijving en vakken van een rek te wijzigen.](afbeeldingen/rek-wijzigen.png)

### Rekoverzicht

De pagina `/rekoverzicht` (menu **Rekoverzicht**) toont elk rek zoals het in de loods staat: een rij per verdieping tot en met de hoogste verdieping met een plaats (verdieping 1 onderaan; een lege verdieping daaronder blijft staan), een kolom per vak tot en met het hoogste vak van dat rek, met een plaatje per plaats. Je ziet in één blik waar nog plek is. Kies een plaatje om de plaats te openen.

![Het Rekoverzicht van één rek, met een plaatje per plaats.](afbeeldingen/rekoverzicht.png)

- **Donkere romp:** de plaats is bezet, met het plaatje van de bootsoort van de boot die er ligt.
- **Lichte romp:** de plaats is vrij, met het plaatje van de eerste bootsoort waarvoor de plaats geschikt is. Is de plaats voor meer soorten geschikt, dan noemt de alternatieve tekst ze allemaal.
- **Gestippelde rand:** een clubplaats zonder boot. Die is niet vrij voor leden. Een clubplaats met een clubboot toont een donkere romp.
- **Alleen een naam:** een bootsoort zonder plaatje, bijvoorbeeld een soort die je zelf toevoegt, toont de naam als tekst. De C11 gebruikt het plaatje van de Canadese kano.
- **Leeg vak:** een plaats zonder bootsoort heeft geen plaatje.

De kleur is niet de enige aanwijzing: elk vak heeft een tekst voor schermlezers, bijvoorbeeld "Plaats A/2/3, Surfski, vrij".

Welke bootsoorten er zijn, stel je in op `/instellingen` (zie Naam, logo en bootsoorten). Een nieuwe installatie begint met kajak, Canadese kano, surfski, C11 en supboard.

## Boten

Op `/boten` staan alle boten met bootsoort, eigenaar en plaats. Een boot heeft een naam, een bootsoort en een eigenaar: een actief lid of de vereniging zelf (clubboot).

![De pagina Boten met het formulier voor een nieuwe boot en de lijst met boten.](afbeeldingen/boten.png)

1. Vul de naam in, kies de bootsoort en de eigenaar. Een oud-lid staat niet in de lijst.
2. Voeg eventueel een foto toe (JPEG, PNG of WebP, hooguit 10 MB).
3. Kies **Boot vastleggen**. Je ziet daarna de pagina van de boot.

Een nieuwe boot heeft nog geen plaats. Op de pagina van de boot wijzig je de naam, de bootsoort en de eigenaar, vervang je de foto of verwijder je de boot. Een boot met een plaats verwijderen weigert de applicatie: geef de plaats eerst vrij.

**Boot wijzigen:** open de boot en pas onder **Boot wijzigen** de naam, de bootsoort of de eigenaar aan (een actief lid of de vereniging) en kies **Boot opslaan**. Een oud-lid kan geen nieuwe eigenaar worden; een boot die al van een oud-lid is, kan wel zo blijven. Heeft de boot een plaats, dan weigert de applicatie een bootsoort die niet bij de plaats past en een wissel tussen een boot van een lid en een clubboot, en zegt ze waarom. Geef de plaats dan eerst vrij. Elke wijziging komt als `boot.gewijzigd` in het log onder de boot, onder het oude en het nieuwe lid en in het log van de bootmutaties. Naam, bootsoort en eigenaar staan er met de oude en de nieuwe waarde. De eigenaar staat er als lidverwijzing (zoals `lid:7`) of als `vereniging`, zonder naam. Wie opslaat zonder iets te veranderen, geeft geen logregel.

![De pagina van een boot met bootsoort, eigenaar, plaats en foto.](afbeeldingen/boot.png)

## De wachtlijst

Een boot van een lid zonder plaats kan op de wachtlijst van zijn bootsoort. Op `/wachtlijst` staat per bootsoort een eigen lijst, met per boot het lid, de aanmelddatum en de wachttijd. De langst wachtende staat bovenaan. Die volgorde is informatie: jij kiest welke boot een vrije plaats krijgt.

![De wachtlijst met per bootsoort de boten, het lid, de aanmelddatum en de wachttijd.](afbeeldingen/wachtlijst.png)

**Een boot op de wachtlijst zetten:** open de boot en kies onder **Wachtlijst** de knop **Op de wachtlijst zetten**. Laat je de aanmelddatum leeg, dan geldt vandaag. Een eerdere datum mag, zodat wie al op een oude lijst stond zijn wachttijd houdt. Een datum in de toekomst weigert de applicatie. De aanmelddatum is daarna niet te wijzigen. Wil je een andere datum, haal de boot dan van de lijst en zet hem er opnieuw op.

![De pagina van een boot zonder plaats met het formulier om de boot op de wachtlijst te zetten.](afbeeldingen/boot-wachtlijst.png)

De applicatie weigert een clubboot, een boot van een oud-lid, een boot met een plaats en een boot die al op de lijst staat. Een boot op de wachtlijst kan geen clubboot worden; haal hem eerst van de lijst. Krijgt een boot een andere bootsoort, dan staat hij op de lijst van die soort, met dezelfde aanmelddatum. Een verwijderde boot gaat van de lijst.

**Van de lijst halen:** kies op `/wachtlijst` of op de pagina van de boot de knop om de boot van de lijst te halen. Drie gevallen gaan vanzelf:

- een boot die een plaats krijgt, gaat van de lijst;
- krijgt de boot een andere eigenaar (een ander lid), dan gaat hij van de lijst. De applicatie meldt dat en het log noemt de reden `andere eigenaar`. Zet de boot er daarna zo nodig opnieuw op;
- wordt de eigenaar oud-lid, dan haalt de eerstvolgende import van leden de boot van de lijst. Het log noemt dan het robottoken van de import als uitvoerder.

Op de pagina van een lid staat per boot of die op de wachtlijst staat en sinds wanneer.

## Een plaats toewijzen of vrijgeven

De applicatie wijst nooit zelf een plaats toe. Jij kiest boot en plaats.

![De pagina van een bezette plaats met boot, eigenaar, adresgegevens en de knop Vrijgeven.](afbeeldingen/plaats-bezet.png)

**Toewijzen:** open een vrije plaats (via `/indeling` of `/vrij`), kies onder **Boot zonder plaats** de boot en kies **Plaats toewijzen**. Bovenaan de keuzelijst staan, bij een gewone plaats, de boten op de wachtlijst van een bootsoort die op de plaats past, de langst wachtende eerst. Daaronder staan de andere boten zonder plaats. De applicatie weigert in deze gevallen en zegt waarom:

- de plaats is bezet, of de boot heeft al een plaats;
- de plaats is niet geschikt voor de bootsoort;
- een clubboot op een gewone plaats, of een boot van een lid op een clubplaats;
- de eigenaar is oud-lid.

**Vanaf de boot:** een boot zonder plaats, op de wachtlijst of niet, kan ook vanaf zijn eigen pagina een plaats krijgen. Kies onder **Plaats toewijzen** een vrije plaats en kies **Wijs toe aan plek**. De lijst toont alleen vrije plaatsen voor de bootsoort, in de volgorde van de loods; voor een clubboot zijn dat de vrije clubplaatsen. Een boot op de wachtlijst gaat daarna van de wachtlijst af. Is er geen vrije plaats, of is de eigenaar oud-lid, dan zegt de pagina dat.

![De pagina van een vrije plaats met de keuze van een boot zonder plaats.](afbeeldingen/plaats-vrij.png)

**Vrijgeven:** open de bezette plaats en kies **Plaats ... vrijgeven**. De boot blijft bestaan, zonder plaats. De plaats blijft vrij tot jij een boot kiest, ook als er een wachtlijst is. Wie twee collega's tegelijk dezelfde plaats laat vrijgeven, krijgt één wijziging in het log.

Na het toewijzen toont de plaats de boot, de eigenaar met lidnummer, adres, telefoon en e-mail, en de link naar de openbare pagina. Die gegevens zijn alleen voor beheerders.

![Een plaats direct na het toewijzen, met de melding dat de boot de plaats heeft gekregen.](afbeeldingen/plaats-toegewezen.png)

## Overzichten

De menubalk bevat drie overzichten. Ze zijn alleen om te lezen; je werkt vanuit de plaats zelf.

| Menu | Adres | Wat je ziet |
|---|---|---|
| Vrije plaatsen | `/vrij` | Vrije plaatsen voor boten van leden, clubplaatsen niet. Filter op bootsoort. |
| Opgezegd | `/opgezegd` | Boten van oud-leden die nog een plaats hebben, de oudste opzegging bovenaan. |
| Gaan opzeggen | `/opzeggend` | Boten met een plaats van leden met een opzegdatum in de toekomst, de vroegste bovenaan. |

![De vrije plaatsen voor kajaks, met rek, aanduiding en geschikte bootsoorten.](afbeeldingen/vrij.png)

![De plaatsen van opgezegde leden met boot, oud-lid en opzegdatum.](afbeeldingen/opgezegd.png)

![Boten van leden die gaan opzeggen, met plaats en opzegdatum.](afbeeldingen/opzeggend.png)

Een lid verhuist van **Gaan opzeggen** naar **Opgezegd** zodra de opzegdatum is bereikt. Open de plaats met de link en geef haar vrij.

## Export naar Excel

Bovenaan `/indeling` staat **Indeling exporteren naar Excel**. Je krijgt het bestand `indeling.xlsx` met een rij per plaats. De kolommen zijn Rek, Code, Status, Bootsoort, Bootnaam, Eigenaar en Lidnummer. Bij een vrije plaats staat in de kolom Bootsoort waarvoor de plaats geschikt is, tussen haakjes. Adres, telefoon, e-mail en foto zitten er bewust niet in.

## Kaartjes printen

Op `/kaartjes` kies je voor welke plaatsen je een kaartje wilt. Vink losse plaatsen aan, een heel rek of **Alle plaatsen**, en kies **Kaartjes maken**. Je krijgt de printpagina `/kaartjes/print` met acht kaartjes per A4, in twee kolommen en vier rijen.

Elk kaartje toont het logo (zonder logo de naam van de vereniging), de aanduiding van de plaats, de bootsoorten waarvoor de plaats geschikt is (bijvoorbeeld "Geschikt voor Kajak/Canadese kano") en een QR-code. Heeft de plaats geen bootsoort, dan valt die regel weg. De omschrijving van het rek en de naam van de eigenaar staan er niet op, zodat je geen nieuw kaartje hoeft te printen als een plaats een andere boot krijgt. Wie op de plaats ligt, staat op de openbare pagina achter de QR-code. Adres, telefoon, e-mail en lidnummer staan nooit op een kaartje.

Print de pagina met **Afdrukken** in de browser, of bewaar haar als pdf. Zet de schaal op 100 procent en de marges op standaard. Knip langs de stippellijnen.

![De printpagina met kaartjes: logo, aanduiding, bootsoorten en QR-code, met stippellijnen om te knippen.](afbeeldingen/kaartjes.png)

De QR-code opent de openbare pagina van de plaats. Krijgt het rek een andere naam, dan blijft het oude kaartje naar dezelfde plaats wijzen; alleen de aanduiding op het kaartje is verouderd. Print dan een nieuw kaartje.

## De openbare pagina

Elke plaats heeft een openbare pagina op `/p/` met een lange, niet te raden sleutel. Je vindt de link op de pagina van de plaats, onder **Openbare pagina**. Wie de link opent, hoeft niet in te loggen en ziet de aanduiding van de plaats, de omschrijving van het rek en of de plaats vrij is, of anders de boot, de eigenaar (bij een clubboot de vereniging) en de foto. Er is geen zoekfunctie en er staan geen adresgegevens op. De pagina gebruikt de naam en het logo van de vereniging.

![De openbare pagina van een plaats met boot, eigenaar en foto.](afbeeldingen/openbaar.png)

## Leden en de import

De ledenlijst komt uit de ledenbron. Je maakt of wijzigt leden niet in de applicatie. De integratiecontainer haalt de lijst dagelijks op en stuurt haar naar de applicatie.

Op `/leden` zoek je op naam of lidnummer. Een lid opent op `/leden/` met zijn boten en plaatsen. Een lid met een opzegdatum van vandaag of eerder heet oud-lid; zijn gegevens en plaatsen blijven staan.

Onder **Aantal boten per bootsoort** staat bij elk lid per bootsoort hoeveel boten een plaats hebben. Een boot op de wachtlijst of zonder plaats telt niet, een clubboot ook niet. Dit zijn de aantallen die de ledenadministratie later kan overnemen; de integratiecontainer haalt dezelfde aantallen op. Terugschrijven naar de ledenbron staat uit.

**Bewaartermijn.** Elke nacht om 04:00 verwijdert de applicatie gegevens die ouder zijn dan 5 jaar. Een oud-lid verdwijnt 5 jaar na de opzegdatum, met zijn boten en foto's. Heeft een boot van het oud-lid nog een plaats, dan blijft alles staan tot je de plaats vrijgeeft. Een regel in een log verdwijnt 5 jaar na de wijziging. Een verwijderd oud-lid komt niet terug met de volgende import. In de logs blijft een verwijderd lid staan als `lid:` met een nummer, zonder naam.

**Een import aanvragen.** Kies op `/leden` bij **Import** de knop **Leden nu ophalen**. De integratiecontainer begint binnen een minuut. Ververs daarna de pagina. Een tweede verzoek terwijl er al een klaarstaat, weigert de applicatie.

![De pagina Leden met de melding dat de import is aangevraagd en de uitkomsten van eerdere imports.](afbeeldingen/leden.png)

**De uitkomst lezen.** De tabel toont de laatste vijf imports met tijdstip, status en resultaat.

| Status | Betekenis |
|---|---|
| aangevraagd | Het verzoek wacht op de integratiecontainer. |
| geslaagd | De import is verwerkt. Het resultaat telt de leden: ontvangen, nieuw, bijgewerkt, overgeslagen, ongeldig en uit_bron (leden die in de bron ontbraken en oud-lid zijn geworden). |
| mislukt | Het resultaat noemt de reden: de ledenbron is niet bereikbaar, het antwoord is onleesbaar, of de bron weigerde de inloggegevens. De ledenlijst is dan niet gewijzigd. |

Blijft een verzoek op aangevraagd staan, dan draait de integratiecontainer waarschijnlijk niet. Meld dat aan wie de installatie beheert.

## Het mutatielog

Elke wijziging van een beheerder en elke wijziging door een robottoken komt in een log, met tijdstip, wie het deed, de handeling, waarop die betrekking had en een paar gegevens. Een log kan niet worden aangepast. Een wijziging van een lid door de import staat er niet in, een wijziging in de botenadministratie als gevolg daarvan wel. De handeling heeft de vorm onderwerp.handeling, zoals `plaats.toegewezen` of `boot.aangemaakt`.

Er zijn twee logs. Elke beheerder ziet ze allebei.

| Log | Menu | Inhoud |
|---|---|---|
| Mutatielog (`/log`) | **Log** | Boten aangemaakt, gewijzigd of verwijderd, een foto toegevoegd of vervangen, een plaats toegewezen of vrijgegeven, een boot op de wachtlijst gezet (`wachtlijst.toegevoegd`, met de aanmelddatum) of eraf gehaald (`wachtlijst.verwijderd`) |
| Technisch log (`/log/techniek`) | **Technisch log** | Tokens, geweigerde API-aanroepen, beheerders en inlogmethodes, instellingen, importverzoeken, de indeling (rekken aanmaken, wijzigen of verwijderen, en plaatsen die erbij komen, wijzigen of verdwijnen), de bootsoorten en de nachtelijke opschoning (`opschoning.uitgevoerd`, met alleen de aantallen) |

Beide tonen per pagina 50 regels, de nieuwste bovenaan; met **Oudere regels** en **Nieuwere regels** blader je verder. Een overzicht toont hooguit 50 regels; toont het er 50, dan opent **Meer in het log** het hele log. Onder een boot staan de mutaties van die boot, onder een lid de mutaties van de boten van dat lid en onder een plaats de toewijzingen en vrijgaven op die plaats. De wachtlijst toont de handelingen op de wachtlijst. De overzichten van vrije plaatsen en van (gaan) opzeggen tonen de toewijzingen en vrijgaven op hun plaatsen. Onder `/indeling` en de schermen voor beheerders, profiel, leden en instellingen staat geen log; zoek die wijzigingen in het technische log.

![Het mutatielog met tijdstip, wie, handeling, betreft en gegevens.](afbeeldingen/log.png)

![Het technische log met een importverzoek, uitnodigingen en inlogs van beheerders.](afbeeldingen/log-techniek.png)

## De technische status

Onder **Status** (`/status`) zie je of de installatie goed draait. Elk onderdeel heeft de status ok, waarschuwing of fout.

| Onderdeel | Wat je ziet | Waarschuwing als |
|---|---|---|
| Database | versie van PostgreSQL en van de migratie | de migratie niet de verwachte is (fout) |
| Worker | laatste heartbeat | die ouder is dan 2 minuten |
| Import van leden | laatste import met resultaat, aantallen en bij een fout de reden; laatste geslaagde import | de laatste import mislukte, of de laatste geslaagde is ouder dan 26 uur |
| Opschoning | laatste opschoning met het aantal verwijderde logregels, leden, boten en foto's | de laatste opschoning mislukte; de worker probeert het de volgende nacht opnieuw |
| API | aan of uit | |
| Bootaantallen | wanneer de integratiecontainer ze voor het laatst ophaalde | |
| Tokens die verlopen | tokens die binnen 31 dagen verlopen, met naam en vervaldatum | er zo'n token is |

Onderaan staat per robottoken de laatste aanroep. De pagina toont geen tokenwaarden, wachtwoorden of gegevens van leden. Dezelfde gegevens staan als JSON op `/status.json`, voor wie de installatie bewaakt.

Een waarschuwing bij de import betekent meestal dat de integratiecontainer niet draait of dat zijn token verlopen is. Een token dat bijna verloopt, vervang je op tijd; dat doet wie de installatie beheert.

![De technische status met per onderdeel de status en een waarschuwing voor een token dat binnenkort verloopt.](afbeeldingen/status.png)

## Tokens voor de API

Met een token gebruik je de API (`/api/v1`) zonder je wachtwoord te delen. Onder **Tokens** (`/tokens`) staan alle tokens van de installatie, met naam, soort, eigenaar of maker, rechten, whitelist, vervaldatum, laatste gebruik en de datum van intrekken. De waarde van een token staat er nooit. Elke beheerder ziet en beheert alle tokens, ook die van een collega.

![De pagina Tokens met een persoonlijk token en een robottoken, hun rechten en de knop Intrekken.](afbeeldingen/tokens.png)

Er zijn twee soorten tokens:

| Soort | Hoort bij | Werkt niet meer als |
|---|---|---|
| Persoonlijk | de beheerder die het maakt | het verloopt, is ingetrokken, of het account geblokkeerd of verwijderd is. Na deblokkeren werkt het weer; na toegang herstellen blijft het werken |
| Robot | een koppeling, zoals de integratiecontainer | het verloopt of is ingetrokken. Het blijft werken als de maker vertrekt; de naam van de maker blijft in het overzicht staan |

### Een token maken

1. Kies **Token maken** (`/tokens/nieuw`).
2. Kies de soort, een naam (a-z, cijfers, punt, - en _) en hoeveel dagen het geldig is: standaard 365, hooguit 1095 (3 jaar).
3. Vink minstens één recht aan. `leden:importeren` staat er niet bij: dat recht geeft wie de installatie beheert met de CLI, aan het robottoken van de integratiecontainer.
4. Vul de IP-whitelist in: adressen of reeksen, gescheiden door komma's. Het formulier vult het netwerk van de integratiecontainer voor. Een robottoken heeft altijd een whitelist; een persoonlijk token zonder whitelist werkt vanaf elk adres dat de installatie doorlaat.
5. Kopieer de waarde die verschijnt. Hij is daarna niet meer te zien; ben je hem kwijt, maak dan een nieuw token en trek het oude in.

![Het formulier Token maken met soort, naam, geldigheid, rechten en whitelist.](afbeeldingen/token-nieuw.png)

![Het scherm na het maken met de tokenwaarde, hier onherkenbaar gemaakt.](afbeeldingen/token-waarde.png)

Een persoonlijk token werkt alleen als wie de installatie beheert de API van buiten heeft opengezet. Zonder dat laat de installatie alleen de integratiecontainer bij de API.

| Recht | Geeft |
|---|---|
| `plaatsen:lezen` | alle plaatsen met rek, clubplaats, bootsoorten en boot |
| `boten:lezen` | alle boten met bootsoort, plaats en naam en lidnummer van de eigenaar |
| `leden:lezen` | alle leden met naam, lidnummer en of het een oud-lid is |
| `wachtlijst:lezen` | de wachtlijst per bootsoort met aanmelddatum |
| `persoonsgegevens` | bij boten, leden en wachtlijst ook adres, telefoon en e-mail, en bij leden de datums van lidmaatschap en opzegging |
| `leden:importeren` | de import van leden, alleen voor de integratiecontainer en alleen met de CLI te geven |
| `bootaantallen:lezen` | het aantal boten per bootsoort per lid |

### Rechten wijzigen en intrekken

Onder **Rechten wijzigen**, onder de lijst, klap je een token uit, pas je de vinkjes aan en kies je **Rechten opslaan**. De nieuwe rechten gelden vanaf de volgende aanroep. Heeft een token `leden:importeren`, dan blijft dat recht staan; het is alleen met de CLI te geven of af te nemen.

![Het blok Rechten wijzigen met een uitgeklapt token en de vinkjes per recht.](afbeeldingen/token-rechten.png)
 **Intrekken** werkt direct: de volgende aanroep met dat token wordt geweigerd. Naam, whitelist en vervaldatum zijn niet te wijzigen; daarvoor maak je een nieuw token.

Maken, rechten wijzigen en intrekken vragen een inlog van hooguit 10 minuten oud. Elke handeling staat in het technische log, zonder de waarde van het token.

## Naam, logo en bootsoorten

Op `/instellingen` pas je de naam van de vereniging aan. Ze staat op elke pagina, ook de openbare. De kleuren zijn vast en niet in te stellen. Opslaan vraagt een inlog van hooguit 10 minuten oud. Het logo zet wie de installatie beheert in de installatie; je ziet het hier alleen.

Onder **Bootsoorten** staan de soorten die je bij boten en plaatsen kiest. Ook elke wijziging hier vraagt een inlog van hooguit 10 minuten oud.

- **Toevoegen:** vul onder **Nieuwe bootsoort** een naam in van 1 tot 50 tekens en kies **Bootsoort toevoegen**. De soort staat daarna in de keuzelijsten voor boten, plaatsen en vrije plaatsen. Zodra een boot van die soort op de wachtlijst staat, heeft de soort een eigen lijst op `/wachtlijst`.
- **Hernoemen:** pas de naam aan en kies **Naam opslaan**. Boten, plaatsen, wachtlijst, export en API tonen direct de nieuwe naam. Toewijzingen en aanmelddata blijven gelijk.
- **Verwijderen:** kies **... verwijderen**. Gebruikt een boot of plaats de soort nog, dan weigert de applicatie en noemt ze de aantallen. Geef die boten een andere soort of verwijder ze, en haal de soort weg bij die plaatsen.

Twee soorten met dezelfde naam kunnen niet, ook niet als ze alleen in hoofdletters verschillen. Toevoegen, hernoemen (met de oude en de nieuwe naam) en verwijderen staan in het technische log.

![De instellingen met de naam, het huidige logo en de bootsoorten.](afbeeldingen/instellingen.png)

## Alle adressen

Wat tussen accolades staat, vult de applicatie zelf in.

| Adres | Pagina |
|---|---|
| `/` | Startpagina |
| `/inloggen` | Inloggen |
| `/inloggen/code` | Code uit de authenticator-app |
| `/uitnodiging/{code}` | Account instellen met een uitnodigingslink |
| `/profiel` | Je inlogmethodes |
| `/beheerders` | Beheerders uitnodigen en beheren |
| `/tokens` | Tokens voor de API |
| `/tokens/nieuw` | Een token maken |
| `/indeling` | Rekken, omschrijvingen en plaatsen |
| `/indeling.xlsx` | Export naar Excel |
| `/rekoverzicht` | Plaatje per plaats, per rek |
| `/kaartjes` | Plaatsen kiezen voor kaartjes |
| `/kaartjes/print` | Kaartjes met QR-code om te printen |
| `/plaatsen/{nummer}` | Een plaats, toewijzen en vrijgeven |
| `/boten` | Boten |
| `/boten/{nummer}` | Een boot, een plaats toewijzen |
| `/vrij` | Vrije plaatsen |
| `/wachtlijst` | Wachtlijst per bootsoort |
| `/opgezegd` | Plaatsen van opgezegde leden |
| `/opzeggend` | Boten van leden die gaan opzeggen |
| `/leden` | Leden en de import |
| `/leden/{nummer}` | Een lid |
| `/log` | Mutatielog: boten en plaatsen |
| `/log/techniek` | Technisch log |
| `/instellingen` | Naam, logo en bootsoorten |
| `/status` | Technische status |
| `/status.json` | Technische status als JSON |
| `/p/{sleutel}` | Openbare pagina van een plaats |
| `/afbeelding/{sleutel}` | Foto op de pagina van een boot of plaats |
| `/logo/{kenmerk}` | Logo in de kopbalk |

Ververs de afbeeldingen met `documentatie/gebruikers/schermafbeeldingen.sh` (start een eigen testomgeving en ruimt die op).
