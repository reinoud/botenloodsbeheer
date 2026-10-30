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
- Later wordt per lid teruggeschreven naar e-boekhouden hoeveel boten van elk type het lid in de loods heeft. Dit wordt voorbereid, maar nog niet geactiveerd.

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
11. Als beheerder wil ik voor één, meerdere of alle plaatsen een kaartje printen met het logo van de vereniging, de code van de plaats, de naam van de eigenaar en een QR-code. De QR-code linkt naar een pagina in de applicatie met de openbare informatie over die plaats: welke boot, de foto en de eigenaar zonder adresgegevens.
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
- Geen vaste huisstijl. Elke vereniging stelt zelf naam, kleuren en logo in.
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
- Er is toegang tot de API van e-boekhouden. Voor nu komt er een stub achter de koppelmodule; de echte koppeling volgt later.
- De link in de QR-code is niet voorspelbaar. Hij bevat geen plaatscode of volgnummer, maar een willekeurige sleutel per plaats, zodat niemand de links van andere plaatsen kan afleiden of doorlopen. De stakeholder vroeg om een "gehashte" URL; een willekeurige sleutel bereikt hetzelfde doel, en een hash van een volgnummer is wel te raden.
