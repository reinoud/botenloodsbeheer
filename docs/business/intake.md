# Intake botenloodsbeheer

Datum: 2026-10-30. Bron: stakeholder, in de startsessie. Dit is de leidende bron voor de business outline en de backlog.

## Aanleiding en probleem

De kanovereniging houdt de indeling van de botenloods nu bij in een spreadsheet. Daarin is niet goed te zien welke boot op welke stallingsplaats hoort, van wie die boot is, welke plaatsen vrij zijn en wie op de wachtlijst staat. De beheerder wil plaatsen toewijzen en vrijgeven, overzichten en printbare kaartjes met QR-code maken, en ledengegevens uit e-boekhouden halen. Leden en bezoekers zien zonder inloggen alleen beperkte gegevens over een plaats. De applicatie moet ook bij andere verenigingen te gebruiken zijn, met een eigen naam, stijl en logo.

De import van de bestaande spreadsheet volgt later en hoort niet bij de eerste versie.

## Techniek en plek

- Python-applicatie in een Docker-container, met PostgreSQL in een tweede container. Beide draaien samen in docker-compose.
- Broncode in `/Users/reinoud/git/botenloods`, een checkout van https://github.com/reinoud/botenloodsbeheer.
- Moderne webinterface die goed werkt op een groot scherm en op een telefoon.
- Te configureren met een eigen stijl, de naam van de vereniging en een logo.

## Domein

- De loods heeft rekken. Elk rek heeft stallingsplaatsen. Elke plaats heeft een unieke naam (nummer of code). Die namen moeten later te wijzigen zijn.
- De indeling van rekken en plaatsen wordt in de applicatie vastgelegd en beheerd, zodat er een visueel overzicht van te maken is.
- Soorten boten: kajak, Canadese kano, surfski, C11, supboard. Sommige plaatsen zijn alleen geschikt voor bepaalde soorten. Welke soorten op welke plaats passen, is te beheren.
- De beheerder wijst plaatsen toe aan boten van leden. Een lid kan meerdere boten hebben en dus meerdere plaatsen.
- Een boot heeft een naam en soms een foto.
- Een eigenaar is een lid of voormalig lid, met naam, adres, telefoonnummer, e-mailadres, datum van lidmaatschap en eventueel datum van opzegging.
- De vereniging heeft eigen boten. Daarvoor zijn plaatsen gereserveerd die niet aan leden toe te wijzen zijn. Welke plaatsen gereserveerd zijn, is te beheren.

## Leden en e-boekhouden

- Leden worden niet in de applicatie bijgehouden, maar regelmatig opgehaald uit e-boekhouden. Elk lid heeft daar een lidnummer.
- De koppeling met e-boekhouden is een aparte module, die makkelijk aan te passen is aan een andere externe bron.
- Later wordt per lid teruggeschreven naar e-boekhouden hoeveel boten van elk type het lid in de loods heeft. Dit wordt voorbereid, maar nog niet geactiveerd. Het terugschrijven wordt nu gebouwd (besluit 2026-11-08, issue #178).

## Gebruikers, beveiliging en logging

- Gebruikers worden lokaal aangemaakt en beheerd. Sommige functies zijn zonder inloggen beschikbaar.
- Een moderne en veilige inlogmethode.
- Elke mutatie wordt gelogd. Onder elk overzicht staat een log met de mutaties die erbij horen.

## User stories van de stakeholder

1. Als beheerder wil ik van een plaats weten welke boot er hoort te liggen en wie de eigenaar is (naam, adres, telefoonnummer, e-mailadres, eventuele foto).
2. Als niet-beheerder wil ik van een plaats weten welke boot er hoort te liggen en wie de eigenaar is (alleen naam).
3. Als beheerder wil ik een overzicht van vrije plaatsen in de loods, te filteren op bootsoort.
4. Als beheerder wil ik een wachtlijst bijhouden voor boten van leden die nog geen plaats hebben.
5. Als beheerder wil ik op het scherm een overzicht van de huidige indeling van de loods.
6. Als beheerder wil ik de huidige indeling naar Excel exporteren.
7. Als beheerder wil ik een plaats toewijzen aan een boot van een lid.
8. Als beheerder wil ik een plaats vrijgeven waar een boot lag.
9. Als beheerder wil ik een overzicht van toegewezen plaatsen van leden die hebben opgezegd.
10. Als beheerder wil ik per lid een lijst van de boten in de loods en hun plaats.
11. Als beheerder wil ik voor één, meerdere of alle plaatsen een kaartje printen met het logo van de vereniging, de code van de plaats, de bootsoorten waarvoor de plaats geschikt is en een QR-code (gewijzigd 2026-11-06, issue #143). De QR-code linkt naar een pagina in de applicatie met de openbare informatie over die plaats: welke boot, de foto en de eigenaar zonder adresgegevens.
12. Als beheerder wil ik de indeling van de loods beheren: rekken, plaatsen, gereserveerde plaatsen voor clubboten en welke bootsoorten op welke plaats passen.

## Besluiten en antwoorden van de stakeholder (2026-10-30)

Deze besluiten gaan voor op de open vragen in `business-outline.md`.

### Omvang en gebruikers

- De loods heeft ongeveer 10 rekken en 160 plaatsen. De vereniging heeft ongeveer 210 leden en 180 boten.
- Er zijn 3 beheerders met dezelfde rechten. Er is geen aparte rol voor systeembeheer.

### Wachtlijst

- Er is een aparte wachtlijst per bootsoort.
- De beheerder ziet hoe lang een boot op de wachtlijst staat. De beheerder kiest zelf welke vrije plaats naar welke boot gaat. De applicatie wijst niet automatisch toe.

### Privacy en bewaren

- Leden hebben ingestemd met het openbaar tonen van alleen hun naam en de foto van hun boot.
- Gegevens van oud-leden en het mutatielog worden 5 jaar bewaard.

### Inrichting

- Eén vereniging per installatie. Een andere vereniging draait een eigen installatie.
- De kleuren volgen de Dajaks-huisstijl en zijn niet in te stellen. Elke vereniging stelt zelf naam en logo in. (Besluit stakeholder 2026-11-06, issue #150; vervangt "geen vaste huisstijl".)
- Hosting met een eigen docker-compose, niet op Hansel.
- Open werk staat in GitHub-issues van `reinoud/botenloodsbeheer`.

### Externe API

- De API is in de configuratie aan en uit te zetten.
- Een ingelogde gebruiker kan persoonlijke tokens maken. Een persoonlijk token is hooguit 3 jaar geldig.
- Er zijn ook robottokens die niet aan een gebruiker gekoppeld zijn.
- Per token is in te stellen welke rechten het heeft.
- Per token is een IP-whitelist in te stellen, met IPv4- en IPv6-adressen.

### Besluiten op de open vragen uit de backlog (2026-10-30)

- Een robottoken is hooguit 3 jaar geldig. Een token dat binnen een maand verloopt, geeft een waarschuwing op de technische statuspagina.
- De API is in de eerste versie alleen-lezen: plaatsen, boten, leden en wachtlijst, met een apart recht voor persoonsgegevens.
- Alle leden hebben ingestemd met het openbaar tonen van hun naam en de foto van hun boot. Instemming per lid hoeft niet te worden vastgelegd.
- De wachttijd op de wachtlijst is informatie. De beheerder kiest vrij.
- Een IP-whitelist is verplicht bij een robottoken en optioneel bij een persoonlijk token.
- De ledensynchronisatie draait dagelijks en is handmatig te starten. Een lid dat uit de bron verdwijnt, wordt oud-lid en wordt niet verwijderd.
- De bewaartermijn van 5 jaar begint voor een oud-lid op de opzegdatum, maar niet zolang het oud-lid nog een boot of plaats in de loods heeft. Voor het log begint de termijn bij de mutatie.
- De Excel-export bevat rek, code, status, bootsoort, bootnaam, naam van de eigenaar en lidnummer. Geen adres, telefoonnummer, e-mailadres of foto. De kolommen kunnen later veranderen.
- Er is toegang tot de API van e-boekhouden. Voor nu komt er een stub achter de koppelmodule; de echte koppeling volgt later. De echte koppeling wordt nu gebouwd (besluit 2026-11-08, issue #178).
- De link in de QR-code is niet voorspelbaar. Hij bevat geen plaatscode of volgnummer, maar een willekeurige sleutel per plaats, zodat niemand de links van andere plaatsen kan afleiden of doorlopen. De stakeholder vroeg om een "gehashte" URL; een willekeurige sleutel bereikt hetzelfde doel, en een hash van een volgnummer is wel te raden.
- Back-ups vallen buiten de verantwoordelijkheid van de applicatie. Ze worden later bij de hosting geregeld.
- De openbare pagina van een plaats is alleen via de QR-link te openen. Er is geen zoekfunctie op plaatscode, omdat iemand anders de namen van leden uit de applicatie kan halen.

### Besluiten op de architectuurvragen (2026-10-30)

- Beheerders loggen in met een passkey of met een wachtwoord plus TOTP. Beide methodes zijn beschikbaar.
- Elke installatie heeft een vaste domeinnaam met HTTPS.
- Een oud-lid wordt opgeschoond 5 jaar na de opzegdatum, zodra geen boot van het oud-lid nog een plaats heeft. De boten en foto's van het oud-lid gaan mee.
- Verdwijnt een lid zonder opzegdatum uit de ledenbron, dan telt de datum waarop de synchronisatie het lid niet meer vond als opzegdatum.
- De API wordt aan- en uitgezet in de installatie, via de omgeving. Niet door de beheerder in de applicatie.
- De ontwerpkeuzes die foundation bij deze besluiten maakte, zijn akkoord: herstel via een andere beheerder trekt alle inlogmethodes en sessies in; na 5 mislukte pogingen 15 minuten geen wachtwoordinlog, passkey blijft werken; geen herstelcodes; TOTP-geheim versleuteld met `TOTP_SLEUTEL`; `API_INGESCHAKELD` standaard uit, wijzigen vraagt een herstart.
- Twee restrisico's uit de review van slice 1a zijn voor nu aanvaard, tot uiterlijk 2027-04-30 of de eerste uitrol in productie: de uitnodigingscode kan in de foutlogs staan (issue #5), en de WebAuthn-challenge staat in een ondertekende cookie (issue #6).

## Besluiten van de stakeholder (2026-10-31)

Deze besluiten gaan voor eerdere besluiten die ermee botsen.

### Na slice 3 (issue #17)

- Het logo staat in de installatie (docker-compose), niet in de applicatie. Het wijzigen van het logo is daardoor geen mutatie en hoeft niet gelogd te worden. Vervangen op 2026-11-08 (issue #186): het logo wordt in de applicatie geüpload. De naam blijft de beheerder in de applicatie instellen; de kleuren zijn vast (besluit 2026-11-06).
- In de Excel-export staat bij een vrije plaats in de kolom Bootsoort "(geschikt voor …)", met de bootsoorten die op die plaats mogen.
- De kolom "Opgezegd op" volgt het besluit van 2026-10-30: verdwijnt een lid zonder opzegdatum uit de ledenbron, dan telt de datum waarop de synchronisatie het lid niet meer vond.

### Imports en exports in een aparte container

- Een aparte container doet alle imports en exports: het ophalen van leden en het terugschrijven van het aantal boten per lid en per bootsoort. Daarmee verdwijnt die functie uit de hoofdapplicatie.
- De container praat alleen met de API van de applicatie, via het interne netwerk van docker-compose. De API is dus niet vanaf internet bereikbaar.
- Een andere vereniging kan de container vervangen door een eigen container voor een andere bron dan e-boekhouden.
- De API staat standaard aan. De standaardwhitelist is het interne netwerk van docker-compose.
- De API is daarmee niet meer alleen-lezen: de container moet leden kunnen bijwerken via de API. Dit vervangt het besluit dat de API in de eerste versie alleen-lezen is en dat `API_INGESCHAKELD` standaard uit staat.
- De beheerdocumentatie beschrijft hoe de container zich bij de API aanmeldt, met voorbeeldcode voor het maken en instellen van een token.

### API van buiten en opzeggingen in de toekomst

- De mogelijkheid om de API bewust van buiten bereikbaar te maken blijft open, als keuze per installatie. Persoonlijke tokens blijven daarom mogelijk.
- e-boekhouden kan leden leveren met een opzegdatum in de toekomst. Heeft zo'n lid boten in de loods, dan ziet de beheerder een lijst met die boten en de opzegdatum, zodat ze vóór die datum weg zijn.
- "(geschikt voor …)" in de Excel-export geldt ook voor een clubplaats zonder boot.
- In "(geschikt voor …)" staan de bootsoorten zoals ze in de applicatie zijn ingevoerd, zonder omzetting naar kleine letters.

### Loggen van de API en de ledenimport

- Geslaagde aanroepen van de API komen niet in het log. De applicatie is niet leidend voor de ledenadministratie.
- Geweigerde aanroepen (geen of een ongeldig token, een adres buiten de whitelist, een ontbrekend recht) komen wel in het log.
- Wijzigingen in leden door de import komen niet in het log, ook niet als één regel per import. De uitkomst van een import en een gemelde fout staan op de statuspagina.
- Mutaties in de botenadministratie komen wel in het log, ook als een import ze veroorzaakt, zoals een boot die van de wachtlijst gaat.

### Export van de botenindeling voor de contributie

- De vereniging rekent de contributie voor een ligplaats af per bootsoort; een Canadese kano is bijvoorbeeld duurder. De applicatie kent geen prijzen. Ze levert per lid het aantal boten per bootsoort; de afrekening gebeurt in de ledenadministratie.
- Alleen boten met een toegewezen plaats tellen mee. Een boot zonder plaats of op de wachtlijst telt niet.
- Clubboten tellen niet mee; ze zijn niet van een lid.

### Proxy en installatie (issue #29)

- Traefik vervangt Nginx. Een gedeelde Traefik draait in een eigen docker-compose-stack op de host; de compose van de botenloods levert alleen de labels voor Traefik en bevat zelf geen Traefik.
- De beheerdocumentatie geeft twee voorbeelden: een docker-compose die kant-en-klare images binnenhaalt en een docker-compose die de images bouwt uit een git-checkout.

### Images (issue #35)

- Bij elke release bouwt GitHub Actions de images en zet ze in ghcr.io: `ghcr.io/reinoud/botenloods-app` en `ghcr.io/reinoud/botenloods-integratie`, alleen voor linux/amd64.
- De packages zijn openbaar, zodat een vereniging ze zonder token binnenhaalt. De repository wordt later ook openbaar.

## Besluiten van de stakeholder (2026-11-01)

### Twee logs (issue #37)

- Er zijn twee logs. Het log van de bootmutaties bevat boot aangemaakt, gewijzigd of verwijderd, foto vervangen en plaats toegewezen of vrijgegeven. Het technische log bevat de rest: tokens, geweigerde API-aanroepen, beheerders en inlogmethodes, instellingen, importverzoeken en de indeling (rekken en plaatsen).
- Handelingen op de wachtlijst (een boot erop zetten of eraf halen) horen bij het log van de bootmutaties: de beheerder van de botenloods doet ze (besluit stakeholder 2026-11-01, issue #41).
- Onder elke boot staan de logregels over die boot. Onder elk lid staan de mutaties over de boten van dat lid.
- Het technische log staat alleen onder een eigen menuoptie, niet onder de overzichten.
- Elke beheerder mag beide logs zien.
- Onder de pagina van een plaats staan de bootmutaties op die plaats (toegewezen, vrijgegeven). Onder `/indeling` staat geen log meer.
- `/log` wordt het log van de bootmutaties. Het technische log krijgt een eigen menuoptie ernaast.

### Aanmelddatum op de wachtlijst (slice 7)

- Een boot die op de wachtlijst komt, krijgt standaard de datum van vandaag als aanmelddatum. De beheerder mag een eerdere datum invullen, zodat wie nu op de lijst in de spreadsheet staat zijn wachttijd houdt. Een datum in de toekomst wordt geweigerd. De aanmelddatum staat in het log.
- De aanmelddatum is achteraf niet te wijzigen. Een andere datum kan alleen door de boot van de lijst te halen en er opnieuw op te zetten.
- Krijgt een boot op de wachtlijst een andere eigenaar, dan gaat de boot van de lijst; de wachttijd hoort bij het lid. De nieuwe eigenaar kan de boot opnieuw op de lijst laten zetten. Dat staat in het log.

### Certificaten

- De gedeelde Traefik vraagt de certificaten aan bij Let's Encrypt.

### Kaartje (2026-11-06, issue #143)

- Het kaartje toont geen omschrijving van het rek en geen naam van de eigenaar, ook geen "vrij" en geen naam van de vereniging bij een clubplaats. De naam van de vereniging staat al bij het logo. Wie op de plaats ligt, staat op de openbare pagina achter de QR-code.
- Het kaartje krijgt de regel "Geschikt voor" met de namen van de bootsoorten van de plaats zoals ze in de applicatie staan, gescheiden door een schuine streep, in de volgorde van de bootsoorten (bijvoorbeeld "Geschikt voor Kajak/Canadese kano"). Heeft de plaats geen bootsoort, dan valt de regel weg.
- De aanduiding van de plaats (zoals `A/1/1`) blijft op het kaartje.

### Koppeling met e-boekhouden (2026-11-08, issue #178)

- De integratiecontainer haalt uit e-boekhouden het lidnummer, de naam, de datum lid sinds en de opzegdatum. Adres, telefoon en e-mail komen niet mee. Het veld met de soort lidmaatschap gebruikt de container alleen om te bepalen wie lid is.
- De container schrijft per lid in vrij veld 10 (`boten_in_loods`) het aantal plaatsen per bootsoort, als JSON-tekst zoals `{"Kajak": 1, "Canadese kano": 2, "Surfski": 0}`. Het schrijven heeft een eigen schakelaar en staat standaard uit.
- Om alleen dat veld te wijzigen mag de container het volledige record lezen en ongewijzigd terugsturen. Het record blijft in de container.
- De container praat met e-boekhouden via de SOAP-bibliotheek `zeep`, met eigen aanroepen (OpenSession, GetRelaties, UpdateRelatie). `eboekhouden-python` valt af, omdat die een bestaande relatie niet kan bijwerken (besluit stakeholder 2026-11-08). Code die alleen voor deze koppeling nodig is, staat alleen in de integratiecontainer.
- Inloggen bij e-boekhouden gaat met omgevingsvariabelen voor gebruikersnaam, code 1 en code 2.
- De bouw test met een nagebootste e-boekhouden. Een proef in de echte administratie, op een testrelatie, gebeurt pas na akkoord van de stakeholder.

### Logo uploaden (2026-11-08, issue #186)

- Een beheerder uploadt, vervangt en verwijdert het logo van de vereniging op de pagina Instellingen. Het logo in de installatie (de map `huisstijl` en de variabele `LOGO_BESTAND`) vervalt.
- Uploaden en verwijderen staan in het technische log, zoals andere instellingen.
- Een logo dat nu in de installatie staat, wordt niet automatisch overgenomen; de beheerder uploadt het één keer.

### Besluiten van de stakeholder (2026-11-08, middag)

- De soorten relatie in e-boekhouden (`Def2`) zijn `actief_gewoon`, `actief_partner`, `actief_jeugdlid` en `opgezegd`. De opzegdatum staat in `Def7`. Een opzegdatum in de toekomst, meestal 31 december van het lopende jaar, hoort bij een lid dat heeft opgezegd maar tot en met die datum lid is (issue #178).
- De live proef van het terugschrijven op een testrelatie mag (issue #178).
- Adres, telefoon en e-mail van leden worden niet meer bewaard. De kolommen en het tokenrecht `persoonsgegevens` verdwijnen met een migratie (issue #180).
- Boten van oud-leden gaan automatisch van de wachtlijst wanneer de integratiecontainer de leden doorgeeft. Er komt geen knop om ze met de hand eraf te halen (issue #176).

### Besluiten van de stakeholder (2026-11-09, issue #180)

- Lid sinds en opzegdatum komen in de leesaanroepen van de API voortaan mee met `leden:lezen`; eerder alleen met `persoonsgegevens`.
- Een token dat alleen `persoonsgegevens` had, wordt bij de migratie ingetrokken, met een regel in het technische log. Tokens met andere rechten verliezen alleen dat recht.
