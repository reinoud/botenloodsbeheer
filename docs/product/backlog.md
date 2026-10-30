# Productbacklog botenloodsbeheer

**Project:** botenloodsbeheer
**Versie:** v0.1.0
**Datum:** 2026-10-30
**Opgesteld door:** Apex, Senior Product Owner
**Status:** Open vragen besloten door de stakeholder op 2026-10-30
**Bronnen, in volgorde van gezag:** `docs/business/intake.md` (inclusief de besluiten van 2026-10-30), `docs/PROJECT-OVERLAY.md` (§5 en §6), `docs/business/business-outline.md`.

## 1. Uitgangspunten

Dit backlog beschrijft wat de beheerder en de bezoeker moeten kunnen. Het kiest geen techniek: de inlogmethode, het datamodel en de bibliotheken zijn aan foundation.

De loods heeft ongeveer 10 rekken, 160 plaatsen, 210 leden en 180 boten. Drie beheerders hebben dezelfde rechten. Er is geen aparte rol voor systeembeheer. Een bezoeker is iedereen die niet is ingelogd, dus ook een lid. Alleen beheerders hebben een account.

Deze eisen gelden voor elke story en staan niet bij elke story herhaald:

- Onder elk overzicht en elk detailscherm voor beheerders staat het log met de mutaties die erbij horen (BLB-025).
- Persoonsgegevens (adres, telefoonnummer, e-mailadres) zijn alleen zichtbaar voor een ingelogde beheerder, en voor een token met het recht daarvoor.
- Elke pagina werkt op een groot scherm en op een telefoon.
- Tests en voorbeeldgegevens gebruiken alleen synthetische gegevens.
- Een bezoeker die een beheerpagina opent, ziet geen gegevens en gaat naar het inlogscherm.

Een story is pas gereed voor bouw als foundation de architectuurvragen heeft beantwoord, aegis de stories over inloggen, tokens en de ledenbron heeft beoordeeld en de gekoppelde open vraag is besloten. Op dit moment is dat voor geen enkele story gebeurd.

### Gezondheid van het backlog

| Meting | Waarde |
|--------|--------|
| Aantal stories | 37 |
| Must | 26 |
| Should | 10 |
| Could | 1 |
| Gereed voor bouw | 0 (wacht op foundation en akkoord stakeholder) |
| Geblokkeerd door een open vraag | Geen. Alle open vragen zijn op 2026-10-30 besloten (§7). |

## 2. Epics

| Epic | Naam | Doel |
|------|------|------|
| EP-01 | Indeling van de loods | Rekken, plaatsen, bootsoorten en clubplaatsen vastleggen en wijzigen |
| EP-02 | Leden en boten | Leden uit een vervangbare bron ophalen en boten van leden en van de vereniging vastleggen |
| EP-03 | Toewijzen en vrijgeven | Plaatsen koppelen aan boten en weer vrijgeven |
| EP-04 | Wachtlijst | Boten zonder plaats per bootsoort laten wachten, met zichtbare wachttijd |
| EP-05 | Overzichten en export | De beheerder een beeld geven van de loods |
| EP-06 | Openbare pagina en kaartjes | Bezoekers beperkte gegevens tonen en kaartjes met QR-code printen |
| EP-07 | Inloggen en beheerders | Toegang tot alles wat niet openbaar is |
| EP-08 | Mutatielog en bewaartermijn | Elke wijziging terug kunnen vinden en gegevens na 5 jaar opruimen |
| EP-09 | Configuratie | Naam, kleuren, logo en de lijst met bootsoorten per vereniging |
| EP-10 | Externe API | Gecontroleerde toegang voor koppelingen, met persoonlijke tokens en robottokens |
| EP-11 | Bewaking van de installatie | Zien of de applicatie gezond is |

## 3. Herkomst van de twaalf intakestories

| Intake | Story in dit backlog |
|--------|----------------------|
| 1 | BLB-012 |
| 2 | BLB-020 |
| 3 | BLB-015 |
| 4 | BLB-013, BLB-014 |
| 5 | BLB-016 |
| 6 | BLB-017 |
| 7 | BLB-010 |
| 8 | BLB-011 |
| 9 | BLB-018 |
| 10 | BLB-019 |
| 11 | BLB-021 |
| 12 | BLB-001, BLB-002, BLB-003, BLB-004 |

## 4. Stories

### EP-01 Indeling van de loods

#### BLB-001 Rekken en plaatsen beheren

Prioriteit: Must. Bron: intake 12. Afhankelijk van: BLB-022.

Als beheerder wil ik rekken en plaatsen aanmaken, wijzigen en verwijderen zodat de indeling in de applicatie klopt met de loods.

- Gegeven een ingelogde beheerder, wanneer die een rek met een naam aanmaakt en daarin plaatsen met een code, dan staan het rek en de plaatsen in de indeling.
- Gegeven een code die al bij een andere plaats hoort, wanneer de beheerder die code opnieuw invoert, dan weigert de applicatie dat met een duidelijke melding.
- Gegeven een plaats of rek waarop een boot is toegewezen, wanneer de beheerder het wil verwijderen, dan weigert de applicatie en wijst op het vrijgeven van de plaats.
- Gegeven een bezoeker, wanneer die de pagina voor het beheer van de indeling opent, dan gaat die naar het inlogscherm en verandert er niets.

#### BLB-002 Geschikte bootsoorten per plaats

Prioriteit: Must. Bron: intake 12. Afhankelijk van: BLB-001.

Als beheerder wil ik per plaats vastleggen welke bootsoorten erop passen (kajak, Canadese kano, surfski, C11, supboard) zodat alleen geschikte boten een plaats krijgen.

- Gegeven een plaats, wanneer de beheerder een of meer bootsoorten aanvinkt, dan slaat de applicatie dit op en toont het bij de plaats.
- Gegeven een plaats met een toegewezen kajak, wanneer de beheerder kajak als geschikte soort weghaalt, dan weigert de applicatie en meldt welke boot er nog ligt.

#### BLB-003 Clubplaatsen reserveren

Prioriteit: Must. Bron: intake 12, overlay §5. Afhankelijk van: BLB-001.

Als beheerder wil ik plaatsen als clubplaats markeren zodat ze gereserveerd blijven voor clubboten en niet naar leden gaan.

- Gegeven een vrije plaats, wanneer de beheerder die als clubplaats markeert, dan staat hij niet meer bij de vrije plaatsen voor leden en is er alleen een clubboot aan toe te wijzen.
- Gegeven een clubplaats, wanneer de beheerder er de boot van een lid aan wil toewijzen, dan weigert de applicatie met de reden dat de plaats gereserveerd is.
- Gegeven een plaats waarop de boot van een lid ligt, wanneer de beheerder de plaats als clubplaats wil markeren, dan weigert de applicatie tot de plaats is vrijgegeven.

#### BLB-004 Plaatscode wijzigen

Prioriteit: Must. Bron: intake (domein), overlay §5. Afhankelijk van: BLB-001.

Als beheerder wil ik de code van een plaats wijzigen zodat de nummering kan meegroeien met de loods.

- Gegeven een toegewezen plaats, wanneer de beheerder de code wijzigt, dan blijft de toewijzing staan en tonen alle schermen de nieuwe code.
- Gegeven een kaartje dat met de oude code is geprint, wanneer een bezoeker de QR-code scant, dan opent de pagina van dezelfde plaats, met de nieuwe code.

### EP-02 Leden en boten

#### BLB-005 Boot vastleggen

Prioriteit: Must. Bron: intake (domein). Afhankelijk van: BLB-006.

Als beheerder wil ik een boot met naam, bootsoort, eigenaar en eventueel een foto vastleggen zodat ik de boot een plaats kan geven.

- Gegeven een lid in de ledenlijst, wanneer de beheerder een boot met naam en bootsoort voor dat lid aanmaakt, dan staat de boot bij het lid. Een lid kan meerdere boten hebben.
- Gegeven een clubboot, wanneer de beheerder die aanmaakt, dan heeft de vereniging de boot als eigenaar en is er geen lid aan gekoppeld.
- Gegeven een bestand dat geen afbeelding is, wanneer de beheerder dat als foto uploadt, dan weigert de applicatie het bestand en blijft de eerdere foto staan.
- Gegeven een boot met een toegewezen plaats, wanneer de beheerder de boot wil verwijderen, dan weigert de applicatie tot de plaats is vrijgegeven.

#### BLB-006 Leden ophalen uit de ledenbron

Prioriteit: Must. Bron: intake (leden en e-boekhouden), overlay §5. Afhankelijk van: BLB-007. Besluit: vraag 6.

Als beheerder wil ik dat de ledenlijst regelmatig uit e-boekhouden wordt opgehaald zodat ik leden niet dubbel bijhoud.

- Gegeven een bereikbare bron, wanneer de synchronisatie draait, dan zijn nieuwe leden aangemaakt en gewijzigde leden bijgewerkt, met het lidnummer als sleutel, en bevat elk lid naam, adres, telefoonnummer, e-mailadres, lidmaatschapsdatum en eventueel opzegdatum.
- Gegeven een bron die niet antwoordt of ongeldige gegevens levert, wanneer de synchronisatie draait, dan blijft de bestaande ledenlijst ongewijzigd en komt de fout in de technische status en het log.
- Gegeven een record zonder lidnummer, wanneer de synchronisatie draait, dan slaat de applicatie dat record over, meldt het en verwerkt de rest.
- Gegeven de ledenlijst, wanneer de beheerder een lid wil aanmaken of wijzigen, dan kan dat in de applicatie niet; de bron is leidend.

#### BLB-007 Ledenbron vervangbaar

Prioriteit: Must. Bron: intake (leden en e-boekhouden), overlay §5. Afhankelijk van: geen.

Als beheerder van een vereniging die niet met e-boekhouden werkt wil ik de ledenbron kunnen vervangen zodat de rest van de applicatie ongewijzigd blijft.

- Gegeven een testbron die leden in het afgesproken formaat levert, wanneer die als ledenbron is ingesteld, dan werkt BLB-006 zonder andere wijzigingen.
- Gegeven een installatie zonder ingestelde bron, wanneer de synchronisatie start, dan meldt de applicatie dat er geen bron is en verandert er niets.
- Gegeven de inloggegevens voor de bron, wanneer een beheerder schermen, logs, exports of de statuspagina opent, dan komen die inloggegevens er nergens in voor.

#### BLB-008 Oud-leden herkennen

Prioriteit: Must. Bron: intake 9, overlay §5. Afhankelijk van: BLB-006.

Als beheerder wil ik dat een lid met een opzegdatum als oud-lid wordt herkend zodat ik plaatsen van opgezegde leden kan opvolgen.

- Gegeven een lid dat in de bron een opzegdatum in het verleden krijgt, wanneer de synchronisatie draait, dan is het lid een oud-lid en blijven de gegevens en toegewezen plaatsen staan.
- Gegeven een boot van een oud-lid zonder plaats, wanneer de beheerder een plaats wil toewijzen, dan weigert de applicatie.
- Gegeven een boot van een lid op de wachtlijst, wanneer dat lid oud-lid wordt, dan verdwijnt de boot van de wachtlijst en staat dat in het log.

#### BLB-009 Terugschrijven voorbereiden, uitgeschakeld

Prioriteit: Should. Bron: intake (leden en e-boekhouden), overlay §5. Afhankelijk van: BLB-005, BLB-007.

Als beheerder wil ik dat het aantal boten per bootsoort per lid klaarstaat voor terugschrijven naar e-boekhouden, zodat de vereniging dit later kan inschakelen zonder nieuwbouw.

- Gegeven de standaardinstelling, wanneer de applicatie draait, dan staat terugschrijven uit en wordt er niets naar de bron gestuurd.
- Gegeven een lid met boten, wanneer de beheerder de lijst per lid opent (BLB-019), dan staat daar het aantal boten per bootsoort: de gegevens die later worden teruggeschreven.
- Gegeven een beheerder die de instelling voor terugschrijven aanzet, wanneer die opslaat, dan meldt de applicatie dat terugschrijven in deze versie niet beschikbaar is en blijft de instelling uit.

### EP-03 Toewijzen en vrijgeven

#### BLB-010 Plaats toewijzen

Prioriteit: Must. Bron: intake 7. Afhankelijk van: BLB-002, BLB-003, BLB-005.

Als beheerder wil ik een plaats toewijzen aan een boot van een lid zodat duidelijk is waar de boot hoort te liggen.

- Gegeven een vrije plaats die geschikt is voor de bootsoort en een boot zonder plaats, wanneer de beheerder toewijst, dan staat de boot op de plaats en is de plaats bezet.
- Gegeven een lid met twee boten, wanneer de beheerder beide een eigen plaats geeft, dan lukt dat. Een lid kan dus meerdere plaatsen hebben.
- Gegeven een plaats die niet geschikt is voor de bootsoort, wanneer de beheerder toewijst, dan weigert de applicatie met de reden.
- Gegeven een bezette plaats, wanneer de beheerder er een tweede boot aan wil toewijzen, dan weigert de applicatie.
- Gegeven een clubplaats, een boot van een oud-lid of een boot die al een plaats heeft, wanneer de beheerder toewijst, dan weigert de applicatie met de reden.

#### BLB-011 Plaats vrijgeven

Prioriteit: Must. Bron: intake 8. Afhankelijk van: BLB-010.

Als beheerder wil ik een plaats vrijgeven waar een boot lag zodat de plaats weer beschikbaar is.

- Gegeven een bezette plaats, wanneer de beheerder die vrijgeeft, dan is de plaats vrij en blijft de boot bestaan, zonder plaats.
- Gegeven een vrijgegeven plaats, wanneer de beheerder de vrije plaatsen opent (BLB-015), dan staat de plaats in de lijst.
- Gegeven een plaats die vrijkomt terwijl er een wachtlijst is, wanneer de beheerder niets doet, dan blijft de plaats vrij tot de beheerder een boot kiest.

#### BLB-012 Plaatsdetail voor de beheerder

Prioriteit: Must. Bron: intake 1. Afhankelijk van: BLB-010.

Als beheerder wil ik van een plaats weten welke boot er hoort te liggen en wie de eigenaar is zodat ik een eigenaar kan bereiken.

- Gegeven een bezette plaats, wanneer de beheerder het plaatsdetail opent, dan ziet die de boot (naam, bootsoort, eventuele foto) en de eigenaar met naam, adres, telefoonnummer en e-mailadres.
- Gegeven een vrije plaats, wanneer de beheerder het detail opent, dan staat er dat de plaats vrij is, met de geschikte bootsoorten.
- Gegeven een clubplaats met een clubboot, wanneer de beheerder het detail opent, dan is de vereniging de eigenaar en staan er geen persoonsgegevens.

### EP-04 Wachtlijst

#### BLB-013 Wachtlijst per bootsoort bijhouden

Prioriteit: Must. Bron: intake 4, besluit wachtlijst, overlay §5. Afhankelijk van: BLB-005.

Als beheerder wil ik boten van leden zonder plaats op een wachtlijst per bootsoort zetten en zien hoe lang ze wachten zodat ik eerlijk kan kiezen wie een plaats krijgt.

- Gegeven een boot zonder plaats, wanneer de beheerder de boot op de wachtlijst zet, dan staat de boot op de wachtlijst van zijn bootsoort, met de datum van aanmelding.
- Gegeven de wachtlijst van een bootsoort, wanneer de beheerder die opent, dan toont de lijst per boot het lid, de aanmelddatum en de wachttijd, met de langst wachtende bovenaan. Lijsten van verschillende bootsoorten staan gescheiden.
- Gegeven een boot die al een plaats heeft of al op de wachtlijst staat, wanneer de beheerder de boot op de wachtlijst wil zetten, dan weigert de applicatie.
- Gegeven een boot op de wachtlijst, wanneer de beheerder die van de lijst haalt, dan is de boot niet meer op de lijst en staat dat in het log.

#### BLB-014 Vanaf de wachtlijst een plaats kiezen

Prioriteit: Must. Bron: besluit wachtlijst, overlay §5. Afhankelijk van: BLB-010, BLB-013.

Als beheerder wil ik zelf kiezen welke vrije plaats naar welke boot op de wachtlijst gaat zodat ik rekening kan houden met de praktijk in de loods.

- Gegeven een vrije plaats en een wachtlijst voor een passende bootsoort, wanneer de beheerder een boot kiest en toewijst, dan staat de boot op de plaats en is de boot van de wachtlijst verwijderd.
- Gegeven een plaats die vrijkomt, wanneer er een passende wachtlijst is, dan wijst de applicatie niet zelf toe.
- Gegeven een plaats die niet geschikt is voor de gekozen boot, wanneer de beheerder toewijst, dan weigert de applicatie en blijft de boot op de wachtlijst.

### EP-05 Overzichten en export

#### BLB-015 Vrije plaatsen per bootsoort

Prioriteit: Must. Bron: intake 3. Afhankelijk van: BLB-002, BLB-011.

Als beheerder wil ik een overzicht van vrije plaatsen, te filteren op bootsoort, zodat ik snel een passende plaats vind.

- Gegeven vrije en bezette plaatsen, wanneer de beheerder het overzicht opent, dan staan alleen vrije plaatsen in de lijst, met rek, code en geschikte bootsoorten. Clubplaatsen staan er niet in.
- Gegeven het filter surfski, wanneer de beheerder dat kiest, dan staan alleen vrije plaatsen die voor surfski geschikt zijn in de lijst.
- Gegeven een filter waarvoor geen vrije plaats bestaat, wanneer de beheerder dat kiest, dan staat er dat er geen vrije plaatsen zijn.

#### BLB-016 Indeling van de loods op het scherm

Prioriteit: Must. Bron: intake 5. Afhankelijk van: BLB-010.

Als beheerder wil ik de huidige indeling per rek op het scherm zien zodat ik de loods in één oogopslag overzie.

- Gegeven de indeling, wanneer de beheerder het overzicht opent, dan staan per rek alle plaatsen met code en status (vrij, bezet, clubplaats), en bij bezette plaatsen de boot en de naam van de eigenaar.
- Gegeven een plaats in het overzicht, wanneer de beheerder erop kiest, dan opent het plaatsdetail (BLB-012).
- Gegeven een telefoon, wanneer de beheerder het overzicht opent, dan is de basisinformatie leesbaar zonder zijwaarts scrollen.

#### BLB-017 Indeling exporteren naar Excel

Prioriteit: Should. Bron: intake 6. Afhankelijk van: BLB-016. Besluit: vraag 8.

Als beheerder wil ik de huidige indeling naar Excel exporteren zodat ik die buiten de applicatie kan gebruiken.

- Gegeven de indeling, wanneer de beheerder de export start, dan komt er een Excel-bestand met een rij per plaats met rek, code, status, bootsoort, bootnaam, naam van de eigenaar en lidnummer (besluit vraag 8; de kolommen kunnen later veranderen).
- Gegeven het bestand, wanneer de beheerder het opent, dan bevat het geen adres, telefoonnummer, e-mailadres of foto.

#### BLB-018 Plaatsen van opgezegde leden

Prioriteit: Must. Bron: intake 9. Afhankelijk van: BLB-008.

Als beheerder wil ik een overzicht van toegewezen plaatsen van leden die hebben opgezegd zodat ik die plaatsen kan opvolgen en vrijgeven.

- Gegeven oud-leden met een toegewezen plaats, wanneer de beheerder het overzicht opent, dan staan per plaats rek, code, boot, naam van het oud-lid en opzegdatum in de lijst, met de oudste opzegging bovenaan.
- Gegeven een plaats in dit overzicht, wanneer de beheerder erop kiest, dan kan die de plaats vrijgeven (BLB-011).

#### BLB-019 Lijst per lid

Prioriteit: Must. Bron: intake 10. Afhankelijk van: BLB-010.

Als beheerder wil ik per lid een lijst van de boten in de loods en hun plaats zodat ik een vraag van een lid direct kan beantwoorden.

- Gegeven een lid met twee boten, waarvan één met een plaats, wanneer de beheerder de lijst opent, dan staan beide boten erin, met bootsoort en plaats of de vermelding dat er geen plaats is, en of de boot op de wachtlijst staat.
- Gegeven 210 leden, wanneer de beheerder op naam of lidnummer zoekt, dan toont de applicatie de passende leden.

### EP-06 Openbare pagina en kaartjes

#### BLB-020 Openbare plaatspagina

Prioriteit: Must. Bron: intake 2, 11, overlay §5. Afhankelijk van: BLB-010. Besluit: vraag 3.

Als bezoeker wil ik van een plaats weten welke boot er hoort te liggen en wie de eigenaar is zodat ik kan zien of een boot op de juiste plaats ligt.

- Gegeven een bezette plaats, wanneer een bezoeker de pagina zonder in te loggen opent, dan ziet die de plaatscode, de naam van de boot, de foto als die er is en alleen de naam van de eigenaar.
- Gegeven de openbare pagina, wanneer een bezoeker de gegevens bekijkt die de pagina ontvangt, dan staan daar geen adres, telefoonnummer, e-mailadres of lidnummer in.
- Gegeven de link naar de openbare pagina van een plaats, wanneer iemand die bekijkt, dan bevat die geen plaatscode, volgnummer of andere afleidbare waarde, maar een willekeurige, niet te voorspellen sleutel per plaats. Wie één link kent, kan daaruit de link van een andere plaats niet afleiden (besluit stakeholder 2026-10-30).
- Gegeven een plaats waarvan de plaatscode wijzigt, wanneer een bezoeker de bestaande link opent, dan werkt die nog.
- Gegeven een plaats die alleen via de QR-link op te vragen is, wanneer een bezoeker een plaatscode probeert in te typen of op te zoeken, dan biedt de applicatie daar geen mogelijkheid voor (besluit stakeholder 2026-10-30: anders zijn de namen van leden uit de applicatie te halen).
- Gegeven een link van een plaats die niet bestaat, wanneer een bezoeker die opent, dan staat er een neutrale melding dat de pagina niet bestaat, zonder gegevens.
- Gegeven een vrije plaats, wanneer een bezoeker de pagina opent, dan staat er dat de plaats vrij is. Bij een clubplaats staan de clubboot en de naam van de vereniging als eigenaar.

#### BLB-021 Kaartjes printen met QR-code

Prioriteit: Must. Bron: intake 11. Afhankelijk van: BLB-020, BLB-027.

Als beheerder wil ik voor één, meerdere of alle plaatsen een kaartje printen met het logo van de vereniging, de plaatscode, de naam van de eigenaar en een QR-code zodat elke plaats in de loods herkenbaar is.

- Gegeven een selectie van een, meerdere of alle plaatsen, wanneer de beheerder het printen start, dan komt er een printbaar document met per plaats een kaartje met logo, plaatscode, naam van de eigenaar en QR-code.
- Gegeven een QR-code op een kaartje, wanneer een bezoeker die scant, dan opent de openbare pagina van die plaats (BLB-020).
- Gegeven een kaartje, wanneer de beheerder het bekijkt, dan staan er geen adres, telefoonnummer of e-mailadres op.
- Gegeven een vrije plaats, wanneer de beheerder het kaartje maakt, dan staat er de plaatscode en de vermelding vrij in plaats van een naam.

### EP-07 Inloggen en beheerders

#### BLB-022 Inloggen en uitloggen

Prioriteit: Must. Bron: intake (gebruikers en beveiliging), overlay §6. Afhankelijk van: geen.

Als beheerder wil ik veilig inloggen zodat alleen beheerders persoonsgegevens en beheerfuncties zien.

- Gegeven een beheerder met een account, wanneer die met juiste gegevens inlogt, dan heeft die toegang tot alle beheerfuncties.
- Gegeven onjuiste inloggegevens, wanneer iemand probeert in te loggen, dan weigert de applicatie zonder te melden welk deel onjuist is.
- Gegeven herhaald mislukte pogingen, wanneer iemand blijft proberen, dan beperkt de applicatie verdere pogingen.
- Gegeven een nieuwe installatie, wanneer de eerste beheerder wordt aangemaakt, dan gebeurt dat zonder vast standaardwachtwoord.
- Besluit stakeholder 2026-10-30 (ADR-001): een beheerder logt in met een passkey of met een wachtwoord plus TOTP; beide zijn beschikbaar.

#### BLB-023 Beheerders beheren

Prioriteit: Must. Bron: intake (gebruikers), besluit omvang. Afhankelijk van: BLB-022.

Als beheerder wil ik accounts van beheerders aanmaken, blokkeren en verwijderen zodat de juiste mensen toegang hebben. Alle beheerders hebben dezelfde rechten.

- Gegeven een ingelogde beheerder, wanneer die een nieuw account aanmaakt, dan kan de nieuwe beheerder inloggen en heeft dezelfde rechten.
- Gegeven het laatste actieve account, wanneer een beheerder dat wil blokkeren of verwijderen, dan weigert de applicatie.
- Gegeven een geblokkeerd account, wanneer die beheerder nog is ingelogd of wil inloggen, dan eindigt de sessie en lukt inloggen niet.
- Gegeven een beheerder die zijn inloggegevens kwijt is, wanneer een andere beheerder toegang herstelt, dan kan de eerste weer inloggen zonder dat iemand het wachtwoord ziet.

### EP-08 Mutatielog en bewaartermijn

#### BLB-024 Elke mutatie loggen

Prioriteit: Must. Bron: intake (logging), overlay §5. Afhankelijk van: BLB-022.

Als beheerder wil ik dat elke wijziging wordt vastgelegd zodat ik kan nagaan hoe een situatie is ontstaan.

- Gegeven een wijziging (aanmaken, wijzigen, verwijderen, toewijzen, vrijgeven, wachtlijst, configuratie, accounts, tokens, synchronisatie), wanneer die slaagt, dan staat er een logregel met tijdstip, wie of wat de wijziging deed, wat er veranderde en waar relevant de oude en nieuwe waarde.
- Gegeven een wijziging via een token, wanneer die slaagt, dan staat de naam van het token in het log. Dit geldt pas als de API kan schrijven; in de eerste versie is de API alleen-lezen (besluit 2026-10-30) en logt BLB-034 de aanroepen.
- Gegeven het log, wanneer een beheerder een regel wil wijzigen of verwijderen, dan kan dat in de applicatie niet.
- Gegeven het log, wanneer een beheerder het bekijkt, dan staan er geen wachtwoorden, tokenwaarden, adressen, telefoonnummers of e-mailadressen in.

#### BLB-025 Log onder elk overzicht

Prioriteit: Must. Bron: intake (logging), overlay §5. Afhankelijk van: BLB-024.

Als beheerder wil ik onder elk overzicht het log met de bijbehorende mutaties zien zodat ik meteen zie wat er is gewijzigd.

- Gegeven een overzicht of detailscherm voor beheerders, wanneer de beheerder het opent, dan staat onder het scherm het log met de mutaties die erbij horen, de nieuwste bovenaan.
- Gegeven een plaats met een wijziging, wanneer de beheerder het detail van die plaats opent, dan staat de wijziging in het log onder het detail.
- Gegeven de openbare pagina, wanneer een bezoeker die opent, dan staat daar geen log.

#### BLB-026 Bewaartermijn van 5 jaar

Prioriteit: Must. Bron: besluit privacy en bewaren, overlay §5. Afhankelijk van: BLB-008, BLB-024. Besluit: vraag 7.

Als beheerder wil ik dat gegevens van oud-leden en het mutatielog na 5 jaar worden verwijderd zodat de vereniging de afgesproken bewaartermijn naleeft.

- Gegeven een oud-lid dat langer dan 5 jaar geleden opzegde en geen plaats of boot meer in de loods heeft, wanneer de opschoning draait, dan zijn de persoonsgegevens van dat oud-lid verwijderd.
- Gegeven een oud-lid dat nog een toegewezen plaats heeft, wanneer de opschoning draait, dan blijven de gegevens staan.
- Gegeven een logregel ouder dan 5 jaar, wanneer de opschoning draait, dan is de regel verwijderd.
- Gegeven een lid dat geen oud-lid is, wanneer de opschoning draait, dan blijven de gegevens altijd staan.
- Gegeven een uitgevoerde opschoning, wanneer een beheerder de technische status opent, dan staan daar het tijdstip en de aantallen verwijderde gegevens, zonder persoonsgegevens.

### EP-09 Configuratie

#### BLB-027 Naam, kleuren en logo instellen

Prioriteit: Must. Bron: intake (aanleiding, techniek), besluit inrichting. Afhankelijk van: BLB-022.

Als beheerder wil ik de naam van de vereniging, de kleuren en het logo instellen zodat de applicatie eruitziet als die van onze vereniging.

- Gegeven een ingelogde beheerder, wanneer die naam, kleuren en logo opslaat, dan tonen alle pagina's, ook de openbare pagina en de kaartjes, de nieuwe naam, kleuren en logo.
- Gegeven een bestand dat geen geldige afbeelding is, wanneer de beheerder dat als logo uploadt, dan weigert de applicatie het en blijft het huidige logo staan.
- Gegeven een kleurkeuze waarbij tekst slecht leesbaar wordt, wanneer de beheerder opslaat, dan waarschuwt de applicatie.
- Gegeven een installatie zonder instellingen, wanneer iemand de applicatie opent, dan staat er een neutrale standaardnaam en een neutrale stijl.

#### BLB-028 Bootsoorten beheren

Prioriteit: Could. Bron: afleiding uit hergebruik door andere verenigingen. Afhankelijk van: BLB-002.

Als beheerder wil ik de lijst met bootsoorten aanpassen zodat een andere vereniging haar eigen soorten gebruikt.

- Gegeven de standaardlijst (kajak, Canadese kano, surfski, C11, supboard), wanneer de beheerder een soort toevoegt, dan is die soort te kiezen bij boten en plaatsen en heeft die een eigen wachtlijst.
- Gegeven een bootsoort waarvoor boten of plaatsen bestaan, wanneer de beheerder de soort wil verwijderen, dan weigert de applicatie.

### EP-10 Externe API

#### BLB-029 API aan en uit zetten

Prioriteit: Should. Bron: besluit externe API, overlay §6. Afhankelijk van: BLB-022.

Als beheerder wil ik dat de externe API in de installatie aan en uit gezet kan worden zodat die alleen bereikbaar is als de vereniging hem gebruikt.

- Gegeven een nieuwe installatie, wanneer er een API-aanroep binnenkomt, dan weigert de applicatie, want de API staat standaard uit.
- Gegeven een installatie waarin de API is aangezet via de omgeving, wanneer een beheerder de applicatie bekijkt, dan is er geen scherm om de API aan of uit te zetten.
- Gegeven een uitgeschakelde API, wanneer een aanroep binnenkomt met een geldig token, dan weigert de applicatie ook dan.
- Gegeven een ingeschakelde API, wanneer een aanroep met een geldig token en voldoende rechten binnenkomt, dan beantwoordt de applicatie die.

#### BLB-030 Persoonlijk token maken

Prioriteit: Should. Bron: besluit externe API. Afhankelijk van: BLB-029, BLB-032.

Als beheerder wil ik een persoonlijk token maken zodat ik de API kan gebruiken zonder mijn wachtwoord te delen.

- Gegeven een ingelogde beheerder, wanneer die een token maakt met een naam, een geldigheidsduur en rechten, dan toont de applicatie de tokenwaarde één keer en daarna nooit meer.
- Gegeven een geldigheidsduur langer dan 3 jaar, wanneer de beheerder opslaat, dan weigert de applicatie.
- Gegeven een beheerder wiens account wordt geblokkeerd of verwijderd, wanneer er een aanroep met diens persoonlijke token binnenkomt, dan weigert de applicatie.

#### BLB-031 Robottoken maken

Prioriteit: Should. Bron: besluit externe API. Afhankelijk van: BLB-029, BLB-032. Besluit: vraag 1.

Als beheerder wil ik een robottoken maken dat niet aan een persoon hangt zodat koppelingen blijven werken als een beheerder vertrekt.

- Gegeven een ingelogde beheerder, wanneer die een robottoken maakt met naam, geldigheidsduur, rechten en IP-whitelist, dan toont de applicatie de tokenwaarde één keer.
- Gegeven een robottoken, wanneer de beheerder die het maakte wordt verwijderd, dan blijft het token werken tot het verloopt of wordt ingetrokken.
- Gegeven een robottoken zonder geldigheidsduur of met een duur boven 3 jaar, wanneer de beheerder opslaat, dan weigert de applicatie.

#### BLB-032 Rechten per token

Prioriteit: Should. Bron: besluit externe API, overlay §6. Afhankelijk van: BLB-029. Besluit: vraag 2.

Als beheerder wil ik per token instellen welke rechten het heeft zodat een koppeling niet meer kan dan nodig is.

- Gegeven een token met alleen het recht om plaatsen te lezen, wanneer het een toewijzing wil maken, dan weigert de applicatie.
- Gegeven een token zonder het recht op persoonsgegevens, wanneer het een boot met eigenaar opvraagt, dan staan daar naam en lidnummer maar geen adres, telefoonnummer of e-mailadres.
- Gegeven het aanmaken van een token, wanneer de beheerder geen enkel recht kiest, dan weigert de applicatie.
- Gegeven een bestaand token, wanneer de beheerder de rechten wijzigt, dan gelden de nieuwe rechten vanaf de volgende aanroep en staat de wijziging in het log.

#### BLB-033 IP-whitelist per token

Prioriteit: Should. Bron: besluit externe API, overlay §6. Afhankelijk van: BLB-030, BLB-031. Besluit: vraag 5.

Als beheerder wil ik per token vastleggen vanaf welke IP-adressen het gebruikt mag worden zodat een gestolen token weinig waard is.

- Gegeven een token met een whitelist, wanneer een aanroep vanaf een adres in de lijst komt, dan beantwoordt de applicatie die, ook voor IPv6-adressen.
- Gegeven een token met een whitelist, wanneer een aanroep vanaf een adres buiten de lijst komt, dan weigert de applicatie ook met een geldig token en komt de poging in het log.
- Gegeven een beheerder die een adres invoert dat geen geldig IPv4- of IPv6-adres is, wanneer die opslaat, dan weigert de applicatie.

#### BLB-034 Aanroepen volgen dezelfde regels als de webinterface

Prioriteit: Should. Bron: overlay §6. Afhankelijk van: BLB-029, BLB-032.

Als beheerder wil ik dat de API dezelfde bedrijfsregels afdwingt, beperkt wordt en wordt gelogd zodat de API geen omweg is.

- Gegeven een aanroep zonder token of met een ongeldig token, wanneer die binnenkomt, dan weigert de applicatie.
- Gegeven een token zonder het recht op persoonsgegevens, wanneer het leden opvraagt, dan levert de applicatie geen adres, telefoonnummer of e-mailadres, net als de webinterface die gegevens alleen aan beheerders toont.
- Gegeven een schrijfaanroep (bijvoorbeeld toewijzen), wanneer die binnenkomt, dan weigert de applicatie, want de API is in de eerste versie alleen-lezen. Komt schrijven later, dan gelden dezelfde bedrijfsregels als in de webinterface.
- Gegeven veel aanroepen van één token in korte tijd, wanneer de grens wordt overschreden, dan beperkt de applicatie dat token en meldt dat.
- Gegeven een aanroep, wanneer die is afgehandeld, dan staan token, tijdstip en uitkomst in het log, zonder tokenwaarde.
- Gegeven een ingeschakelde API, wanneer een beheerder de beschrijving opent, dan staan alle beschikbare functies in de beschrijving.

#### BLB-035 Tokens overzien en intrekken

Prioriteit: Should. Bron: besluit externe API. Afhankelijk van: BLB-030, BLB-031.

Als beheerder wil ik alle tokens zien en intrekken zodat een lek of een vertrek snel te dichten is.

- Gegeven bestaande tokens, wanneer de beheerder het overzicht opent, dan staan per token naam, soort (persoonlijk of robot), eigenaar, rechten, vervaldatum en laatste gebruik, maar nooit de waarde.
- Gegeven drie beheerders met gelijke rechten, wanneer één beheerder een token van een ander intrekt, dan lukt dat en staat het in het log.

### EP-11 Bewaking van de installatie

#### BLB-036 Health endpoints

Prioriteit: Must. Bron: overlay §6. Afhankelijk van: geen.

Als beheerder wil ik dat de applicatie aangeeft of ze leeft en gereed is zodat een storing snel opvalt.

- Gegeven een draaiende applicatie, wanneer iemand het levend-signaal opvraagt, dan antwoordt de applicatie zonder inloggen en zonder gegevens over leden of boten.
- Gegeven een onbereikbare database, wanneer iemand het gereed-signaal opvraagt, dan meldt de applicatie dat ze niet gereed is.

#### BLB-037 Technische statuspagina

Prioriteit: Should. Bron: overlay §6. Afhankelijk van: BLB-022, BLB-006, BLB-026.

Als beheerder wil ik een technische statuspagina zodat ik de toestand van de installatie kan beoordelen.

- Gegeven een ingelogde beheerder, wanneer die de pagina opent, dan ziet die in leesbare vorm en als JSON de applicatieversie, de databasestatus, de laatste ledensynchronisatie met resultaat, de laatste opschoning, en of de API en het terugschrijven aan of uit staan.
- Gegeven een mislukte ledensynchronisatie, wanneer de beheerder de pagina opent, dan staat de foutmelding erop, zonder inloggegevens van de bron.
- Gegeven de statuspagina, wanneer de beheerder die bekijkt, dan staan er geen tokens, wachtwoorden of gegevens van leden op.
- Gegeven een persoonlijk token of robottoken dat binnen een maand verloopt, wanneer de beheerder de pagina opent, dan staat er een waarschuwing met de naam van het token en de vervaldatum, zonder de tokenwaarde.

## 5. Voorstel voor de volgorde van slices

| Slice | Stories | Doel |
|-------|---------|------|
| 1 | BLB-022, 001, 007, 006, 005, 010, 012, 020, 024, 025 | Een beheerder logt in, legt een rek, een plaats en een boot van een lid uit de ledenbron vast, wijst de plaats toe, en een bezoeker ziet de openbare pagina, met een log |
| 2 | BLB-002, 003, 004, 008, 011, 023, 036 | De indeling is volledig te beheren, plaatsen zijn vrij te geven, oud-leden worden herkend en meerdere beheerders werken samen |
| 3 | BLB-015, 016, 019, 018, 017, 027 | De beheerder overziet de loods, exporteert naar Excel en stelt naam, kleuren en logo in |
| 4 | BLB-013, 014 | Boten wachten per bootsoort en de beheerder kiest zelf de plaats |
| 5 | BLB-021 | Elke plaats krijgt een printbaar kaartje met QR-code |
| 6 | BLB-026, 037, 009 | De bewaartermijn werkt, de installatie is te bewaken en het terugschrijven staat klaar maar uit |
| 7 | BLB-029 tot en met 035 | Koppelingen gebruiken de API met tokens, rechten en IP-whitelist |
| 8 | BLB-028 | Een andere vereniging past de bootsoorten aan |

Slice 1 is het kleinste stuk dat echt werkt: één beheerder, één rek, één boot, één openbare pagina. Het risico zit in BLB-006: toegang tot de API van e-boekhouden is niet bevestigd. Forge kan met een testbron beginnen (BLB-007).

Het log uit slice 1 bevat vanaf het begin de datum van elke mutatie, zodat opschonen in slice 6 mogelijk is.

## 6. Won't Have in deze cyclus

| Onderwerp | Reden |
|-----------|-------|
| Import van de bestaande spreadsheet | Besluit stakeholder: volgt later |
| Daadwerkelijk terugschrijven naar e-boekhouden | Alleen voorbereid (BLB-009) |
| Leden aanmaken of wijzigen in de applicatie | De ledenbron is leidend |
| Meerdere verenigingen in één installatie | Besluit stakeholder: één vereniging per installatie |
| Automatische toewijzing van plaatsen | Besluit stakeholder: de beheerder kiest zelf |
| Aparte rol voor systeembeheer | Besluit stakeholder: drie gelijke beheerders |

## 7. Besluiten op de open vragen

De stakeholder heeft deze vragen op 2026-10-30 besloten. Ze staan ook in `docs/business/intake.md`.

| Nr | Vraag | Besluit | Raakt |
|----|-------|---------|-------|
| 1 | Wat is de maximale geldigheid van een robottoken? | 3 jaar. Een token zonder einddatum is niet toegestaan. Een token dat binnen een maand verloopt, geeft een waarschuwing op de technische statuspagina. | BLB-031, BLB-037 |
| 2 | Welke functies biedt de API in de eerste versie, en welke rechten zijn er per token? | Eerst alleen lezen: plaatsen, boten, leden, wachtlijst, met een apart recht voor persoonsgegevens. Schrijven volgt in een latere story. | BLB-032, BLB-034 |
| 3 | Moet de instemming per lid worden vastgelegd? | Nee. Alle leden hebben ingestemd met het openbaar tonen van hun naam en de foto van hun boot. | BLB-020, BLB-021 |
| 4 | Telt de volgorde op de wachtlijst mee? | Nee. De wachttijd is informatie; de beheerder kiest vrij en de applicatie legt geen reden vast. | BLB-013, BLB-014 |
| 5 | Is een IP-whitelist verplicht? | Verplicht bij een robottoken, optioneel bij een persoonlijk token. Een lege lijst bij een robottoken weigert de applicatie. | BLB-031, BLB-033 |
| 6 | Hoe vaak synchroniseren we met de ledenbron? | Dagelijks, en handmatig te starten. Een verdwenen lid wordt oud-lid en wordt niet verwijderd. | BLB-006, BLB-008 |
| 7 | Wanneer begint de termijn van 5 jaar? | Voor een oud-lid op de opzegdatum, maar niet zolang het oud-lid nog een boot of plaats in de loods heeft. Voor het log vanaf de mutatie. | BLB-026 |
| 8 | Welke kolommen staan in de Excel-export? | Rek, code, status, bootsoort, bootnaam, naam van de eigenaar en lidnummer. Geen adres, telefoonnummer, e-mailadres of foto. De kolommen kunnen later veranderen. | BLB-017 |

## 8. Aannames

- Een plaats heeft ten hoogste één boot, en een boot heeft ten hoogste één plaats. Verplaatsen is vrijgeven gevolgd door toewijzen.
- Een plaats blijft toegewezen na opzegging van het lid tot de beheerder haar vrijgeeft. De applicatie geeft niet automatisch vrij.
- Een boot heeft hooguit één foto. De toegestane bestandsgrootte en bestandstypen bepaalt foundation.
- De vijf bootsoorten uit de intake zijn de startlijst. Aanpassen is BLB-028.
- Besluit stakeholder 2026-10-30: de API gaat aan en uit in de installatie, via een omgevingsvariabele (ADR-009), niet in de applicatie.
- Een IP-whitelist bevat adressen en adresreeksen, zowel IPv4 als IPv6.
- Een wachttijd telt vanaf de dag van aanmelding op de wachtlijst.
