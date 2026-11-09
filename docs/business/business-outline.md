# Business outline botenloodsbeheer

Datum: 2026-10-30. Bron: `docs/business/intake.md` (leidend en enige bron).

## 1. Aanleiding en probleem

De kanovereniging houdt de indeling van de botenloods bij in een spreadsheet. Daarin is niet goed te zien welke boot op welke stallingsplaats hoort, van wie die boot is, welke plaatsen vrij zijn en wie op de wachtlijst staat.

De beheerder wil plaatsen toewijzen en vrijgeven, overzichten en printbare kaartjes met QR-code maken, en ledengegevens uit e-boekhouden halen. Leden en bezoekers zien zonder inloggen alleen beperkte gegevens over een plaats. De applicatie moet ook bij andere verenigingen te gebruiken zijn, met een eigen naam, stijl en logo.

## 2. Doelgroepen en gebruikers

De beheerder is de hoofdgebruiker. Die legt de indeling van rekken en plaatsen vast, wijst plaatsen toe, houdt de wachtlijst bij, print kaartjes en exporteert naar Excel. De beheerder is ook de enige die adres, telefoonnummer en e-mailadres van eigenaren ziet.

De niet-ingelogde bezoeker of het lid scant de QR-code op een plaats of opent de pagina via een link. Die ziet welke boot er hoort te liggen, de foto en alleen de naam van de eigenaar. Er is geen account nodig.

Een systeembeheerder is een mogelijke derde rol: iemand die de applicatie draait, gebruikers aanmaakt en updates doorvoert. De intake noemt die rol niet. Of dit dezelfde persoon is als de beheerder, is een open vraag.

Andere verenigingen zijn hergebruikers. Voor hen telt dat naam, stijl en logo aanpasbaar zijn en dat de koppeling met een externe ledenbron te vervangen is. Of zij een eigen installatie krijgen of één gedeelde omgeving gebruiken, is een open besluit van de stakeholder.

## 3. Waardepropositie

Voor de beheerder: bij elke plaats is in één oogopslag te zien wie de eigenaar is, welke boot er ligt en of de plaats vrij is. Toewijzen en vrijgeven gebeurt op één plek, met een log van elke wijziging.

Voor leden en bezoekers: een geprinte QR-code op de plaats geeft direct de openbare gegevens, zonder inloggen en zonder dat adresgegevens zichtbaar zijn.

Voor de vereniging: de ledengegevens komen uit e-boekhouden en worden niet dubbel bijgehouden. Dat is de bron die de vereniging al gebruikt.

Voor andere verenigingen: dezelfde oplossing met eigen naam, stijl en logo.

## 4. Lichte business case

De vereniging is een vrijwilligersorganisatie. De waarde zit in tijd, minder fouten en overzicht, niet in omzet. Alle getallen hieronder zijn aannames en geen metingen.

Waarde:
- Tijd. Aanname: de beheerder besteedt nu enkele uren per maand aan zoeken, bijwerken en navragen in de spreadsheet, met pieken bij het begin van het seizoen. Een overzicht en filters kunnen een groot deel daarvan weghalen. Orde van grootte: tientallen uren per jaar.
- Fouten. Aanname: dubbele toewijzingen, boten op de verkeerde plaats en plaatsen van opgezegde leden die blijven staan komen nu voor. Elke fout kost een telefoontje of een gesprek tussen vrijwilligers.
- Overzicht. Vrije plaatsen per bootsoort, de wachtlijst en plaatsen van opgezegde leden zijn nu niet snel te zien. Daardoor blijft stallingsruimte mogelijk ongebruikt terwijl er een wachtlijst is.
- Hergebruik. Elke andere vereniging die de applicatie gebruikt, deelt de kosten van bouw en onderhoud.

Kosten:
- Bouw. Eenmalig, omvang afhankelijk van de eerste versie in sectie 5. De stakeholder bepaalt of dit eigen tijd of ingekochte tijd is.
- Hosting. Doorlopend, aanname: klein en in de orde van tientallen euro's per maand. De keuze voor hosting is open.
- Onderhoud. Doorlopend: beveiligingsupdates, aanpassing bij wijzigingen in de e-boekhouden-API, nieuwe gebruikers. Dit is vermoedelijk de grootste kostenpost op termijn, omdat het van vrijwilligers afhangt.

De business case is positief als het beheer beperkt blijft tot enkele uren per jaar en als de tijdwinst voor de beheerder reëel is. Zijn die aannames onjuist, dan weegt het onderhoud zwaarder dan de winst. De stakeholder kan dit toetsen door nu de huidige tijdsbesteding te schatten.

## 5. Scope eerste versie en buiten scope

In de eerste versie:
- Rekken, plaatsen, gereserveerde plaatsen voor clubboten en geschikte bootsoorten per plaats beheren, met wijzigbare plaatsnamen.
- Boten (naam, soort, foto) en eigenaren vastleggen; ledengegevens ophalen uit e-boekhouden via een aparte module.
- Plaatsen toewijzen en vrijgeven, vrije plaatsen filteren op bootsoort, wachtlijst bijhouden.
- Overzichten: indeling op het scherm, lijst per lid, plaatsen van opgezegde leden, export naar Excel.
- Printbare kaartjes met logo, plaatscode, eigenaarsnaam en QR-code, met een openbare pagina per plaats.
- Lokaal gebruikersbeheer met een veilige inlogmethode, en een log van elke mutatie onder het bijbehorende overzicht.
- Instelbare naam, stijl en logo per vereniging.
- Terugschrijven naar e-boekhouden van het aantal plaatsen per bootsoort per lid, achter een schakelaar (besluit stakeholder 2026-11-08, #178).

Buiten de eerste versie:
- Import van de bestaande spreadsheet.
- Het bijhouden van leden in de applicatie zelf.

Open besluiten van de stakeholder die de scope raken: tenancy, huisstijl en hosting. Dit document kiest daarin niet.

## 6. Risico's en aannames

Risico's:
- Privacy. De applicatie bevat lidnummer, naam en lidmaatschapsdata van leden en voormalige leden, dus persoonsgegevens onder de AVG. Adres, telefoon en e-mail worden sinds 2026-11-09 niet meer bewaard (#180). De openbare pagina mag geen adresgegevens tonen. Bewaartermijnen en de grondslag voor het tonen van de eigenaarsnaam zijn nog niet vastgesteld.
- Afhankelijkheid van de e-boekhouden-API. Een wijziging of storing aan die kant raakt de ledenlijst. De aparte koppelmodule beperkt de schade, maar haalt het risico niet weg.
- Beschikbaarheid van vrijwilligers. Beheer en onderhoud hangen aan een of twee personen. Vertrekt de beheerder, dan staat de applicatie stil.
- Datakwaliteit. De spreadsheet wordt later geïmporteerd. Tot die tijd moet de beheerder de indeling handmatig opnieuw invoeren, met kans op fouten.
- Hergebruik. Elke extra vereniging vergroot de eisen aan beheer, ondersteuning en gegevensscheiding.

Aannames:
- E-boekhouden blijft de bron van ledengegevens en biedt de benodigde gegevens via een API.
- De loods heeft een beperkt aantal rekken en plaatsen, in de orde van tientallen tot enkele honderden.
- Er zijn weinig beheerders; leden en bezoekers loggen niet in.
- De eerste vereniging is de stakeholder zelf; andere verenigingen volgen later.

## 7. Open vragen voor de stakeholder

1. Krijgt elke vereniging een eigen installatie, of gebruiken meerdere verenigingen één omgeving (tenancy)?
2. Welke huisstijl geldt voor de eerste vereniging, en wie levert logo en kleuren?
3. Waar en door wie wordt de applicatie gehost (hosting)?
4. Hoeveel rekken, plaatsen, leden en boten telt de loods ongeveer?
5. Hoeveel beheerders zijn er, en hebben zij allemaal dezelfde rechten?
6. Welke regels gelden voor de wachtlijst, zoals volgorde van aanmelding en wachtlijst per bootsoort?
7. Hebben leden ingestemd met het openbaar tonen van hun naam en de foto van hun boot, en hoe leggen we dat vast?
8. Hoe lang bewaart de vereniging gegevens van voormalige leden en de log van mutaties?
