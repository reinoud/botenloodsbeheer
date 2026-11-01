# Productbacklog botenloodsbeheer

**Project:** botenloodsbeheer
**Versie:** v0.3.12
**Datum:** 2026-10-31
**Opgesteld door:** Apex, Senior Product Owner
**Status:** Slice 1 tot en met 6 af; besluiten van de stakeholder van 2026-10-31 en ADR-012 verwerkt
**Bronnen, in volgorde van gezag:** `docs/business/intake.md` (inclusief de besluiten van 2026-10-30 en 2026-10-31), `docs/PROJECT-OVERLAY.md` (§5 en §6), `docs/business/business-outline.md`. Voor het ontwerp: `docs/architecture/architectuur.md` v0.3.0 en ADR-012.

## 1. Uitgangspunten

Dit backlog beschrijft wat de beheerder en de bezoeker moeten kunnen. Het kiest geen techniek: de inlogmethode, het datamodel en de bibliotheken zijn aan foundation.

De loods heeft ongeveer 10 rekken, 160 plaatsen, 210 leden en 180 boten. Drie beheerders hebben dezelfde rechten. Er is geen aparte rol voor systeembeheer. Een bezoeker is iedereen die niet is ingelogd, dus ook een lid. Alleen beheerders hebben een account.

Deze eisen gelden voor elke story en staan niet bij elke story herhaald:

- Onder elk overzicht en elk detailscherm voor beheerders staat het log met de mutaties die erbij horen (BLB-025).
- Persoonsgegevens (adres, telefoonnummer, e-mailadres) zijn alleen zichtbaar voor een ingelogde beheerder, en voor een token met het recht daarvoor.
- Elke pagina werkt op een groot scherm en op een telefoon.
- Tests en voorbeeldgegevens gebruiken alleen synthetische gegevens.
- Een bezoeker die een beheerpagina opent, ziet geen gegevens en gaat naar het inlogscherm.

Een story is pas gereed voor bouw als foundation de architectuurvragen heeft beantwoord en de gekoppelde open vraag is besloten. Aegis beoordeelt de stories over inloggen, tokens en de import van leden bij de review van de slice. Een criterium met een slicenummer erachter wordt in die slice gebouwd of opnieuw getoetst; zonder nummer hoort het bij de slice van de story in §5.

### Gezondheid van het backlog

| Meting | Waarde |
|--------|--------|
| Aantal stories | 42 |
| Must | 34 |
| Should | 7 |
| Could | 1 |
| Af (slice 1 tot en met 3) | 24, waarvan BLB-006, 007, 008, 017, 024 en 027 nieuwe criteria hebben voor slice 4 of 6 |
| Gereed voor bouw | Slice 4 tot en met 11 (§5) |
| Geblokkeerd door een open vraag | Geen story. Vraag 17 blokkeert de eerste uitrol in productie (§7). |

## 2. Epics

| Epic | Naam | Doel |
|------|------|------|
| EP-01 | Indeling van de loods | Rekken, plaatsen, bootsoorten en clubplaatsen vastleggen en wijzigen |
| EP-02 | Leden en boten | Leden via een vervangbare integratiecontainer ophalen en boten van leden en van de vereniging vastleggen |
| EP-03 | Toewijzen en vrijgeven | Plaatsen koppelen aan boten en weer vrijgeven |
| EP-04 | Wachtlijst | Boten zonder plaats per bootsoort laten wachten, met zichtbare wachttijd |
| EP-05 | Overzichten en export | De beheerder een beeld geven van de loods |
| EP-06 | Openbare pagina en kaartjes | Bezoekers beperkte gegevens tonen en kaartjes met QR-code printen |
| EP-07 | Inloggen en beheerders | Toegang tot alles wat niet openbaar is |
| EP-08 | Mutatielog en bewaartermijn | Elke wijziging terug kunnen vinden en gegevens na 5 jaar opruimen |
| EP-09 | Configuratie | Naam en kleuren in de applicatie, het logo uit de installatie, en de lijst met bootsoorten per vereniging |
| EP-10 | API | Gecontroleerde toegang over het interne netwerk voor de integratiecontainer en andere koppelingen, met robottokens en persoonlijke tokens |
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

Prioriteit: Must. Bron: intake (leden en e-boekhouden, besluiten 2026-10-31), overlay §5, ADR-004, ADR-012. Afhankelijk van: BLB-007, BLB-039. Besluit: vraag 6.

Als beheerder wil ik dat de ledenlijst dagelijks en op verzoek uit e-boekhouden wordt opgehaald zodat ik leden niet dubbel bijhoud.

Gebouwd in slice 1 met de synchronisatie in de applicatie. Sinds 2026-10-31 haalt de integratiecontainer de leden op en stuurt hij ze met `PUT /api/v1/leden`; alle criteria worden in slice 6 opnieuw getoetst via die route.

- Gegeven een bereikbare bron, wanneer de import draait, dan zijn nieuwe leden aangemaakt en gewijzigde leden bijgewerkt, met het lidnummer als sleutel, en bevat elk lid naam, adres, telefoonnummer, e-mailadres, lidmaatschapsdatum en eventueel opzegdatum. (slice 6)
- Gegeven een integratiecontainer met een ingestelde `SYNC_TIJDSTIP`, wanneer dat tijdstip is gepasseerd en die dag nog geen import slaagde, dan start de import. (slice 6)
- Gegeven een bron die niet antwoordt of ongeldige gegevens levert, wanneer de import draait, dan blijft de ledenlijst ongewijzigd, meldt de container de fout met een reden uit de vaste lijst (`bron_onbereikbaar`, `bron_onleesbaar`, `bron_geweigerd`), en staat die reden op de statuspagina. Na een fout probeert de container hooguit één keer per uur opnieuw; een verzoek van een beheerder wacht niet (besluit 2026-10-31, #28), behalve na een fout van de API zelf (zoals een geweigerd token), want dan blijft het verzoek open. (slice 6)
- Gegeven een record zonder lidnummer, wanneer de import draait, dan slaat de applicatie dat record over, telt het als ongeldig zonder de inhoud te loggen, en verwerkt de rest. (slice 6)
- Gegeven een beheerder die in de webinterface een import aanvraagt, wanneer de integratiecontainer draait, dan begint de import binnen een minuut en toont de pagina na verversen de uitkomst van die import. (slice 6)
- Gegeven een lopende import, wanneer er een tweede `PUT /api/v1/leden` binnenkomt, dan weigert de API die met 409 en verandert er niets aan de lopende import. (slice 6)
- Gegeven de ledenlijst, wanneer de beheerder een lid wil aanmaken of wijzigen, dan kan dat in de webinterface niet; de bron is leidend.

#### BLB-007 Integratiecontainer vervangbaar

Prioriteit: Must. Bron: intake (leden en e-boekhouden, besluiten 2026-10-31), overlay §5, ADR-004, ADR-012. Afhankelijk van: BLB-039.

Als beheerder van een vereniging die niet met e-boekhouden werkt wil ik de integratiecontainer door een eigen container voor een andere bron kunnen vervangen zodat de applicatie ongewijzigd blijft.

Gebouwd in slice 1 als vervangbare ledenbron in de applicatie. Sinds 2026-10-31 is de container het vervangbare deel; alle criteria horen bij slice 6.

- Gegeven een eigen container die alleen de aanroepen uit de beheerdocumentatie (BLB-040) gebruikt, wanneer die de leden met `PUT /api/v1/leden` stuurt, dan werkt BLB-006 zonder wijziging in de applicatie. De test gebruikt de stub met een JSON-bestand. (slice 6)
- Gegeven een integratiecontainer zonder ingestelde bron, wanneer die start, dan meldt hij in zijn log dat er geen bron is, roept hij de API niet aan en verandert er niets. (slice 6)
- Gegeven een verzoek waarin `leden` geen lijst is of meer dan 5000 records heeft, of dat groter is dan 2 MB, wanneer het binnenkomt, dan weigert de API het (422 of 413) en verandert er niets. (slice 6)
- Gegeven een container die een halve lijst stuurt, wanneer de import draait, dan houdt de veiligheidsgrens uit BLB-034 de import tegen. (slice 6)
- Gegeven de inloggegevens voor de bron, wanneer een beheerder schermen, logs, exports of de statuspagina van de applicatie opent, dan komen die inloggegevens er nergens in voor; ze staan alleen in de omgeving van de integratiecontainer. (slice 6)

#### BLB-008 Oud-leden herkennen

Prioriteit: Must. Bron: intake 9, besluiten 2026-10-30, overlay §5, ADR-004. Afhankelijk van: BLB-006.

Als beheerder wil ik dat een lid met een opzegdatum als oud-lid wordt herkend zodat ik plaatsen van opgezegde leden kan opvolgen.

Gebouwd in slice 2. Alle criteria worden in slice 6 opnieuw getoetst via `PUT /api/v1/leden`; het derde criterium hangt ook af van de wachtlijst (BLB-013, slice 7).

- Gegeven een lid dat in de bron een opzegdatum in het verleden krijgt, wanneer de import draait, dan is het lid een oud-lid en blijven de gegevens en toegewezen plaatsen staan. (slice 6)
- Gegeven een lid dat in de lijst van een import ontbreekt, wanneer de import slaagt, dan wordt het lid oud-lid met de datum van die import als opzegdatum en wordt het niet verwijderd. (slice 6)
- Gegeven een boot van een lid op de wachtlijst, wanneer dat lid oud-lid wordt, dan verdwijnt de boot van de wachtlijst en staat dat in het log. (slice 7, na BLB-013)
- Gegeven een record met een opzegdatum van meer dan 5 jaar geleden van een lid dat niet in de applicatie staat, wanneer de import draait, dan maakt de applicatie dat lid niet aan. Zo komt een opgeschoond oud-lid niet terug. (slice 6)
- Gegeven een boot van een oud-lid zonder plaats, wanneer de beheerder een plaats wil toewijzen, dan weigert de applicatie.

#### BLB-009 Terugschrijven voorbereiden, uitgeschakeld

Prioriteit: Should. Bron: intake (leden en e-boekhouden, besluiten 2026-10-31), overlay §5, ADR-004, ADR-012. Afhankelijk van: BLB-005, BLB-031, BLB-039.

Als beheerder wil ik dat het aantal boten per bootsoort per lid klaarstaat voor terugschrijven naar e-boekhouden, zodat de vereniging dit later kan inschakelen zonder nieuwbouw.

- Gegeven een standaardinstallatie, wanneer de integratiecontainer draait, dan stuurt hij niets naar de bron: terugschrijven is in de container niet beschikbaar en er draait geen taak die terugschrijft.
- Gegeven een lid met boten, wanneer de beheerder de lijst per lid opent (BLB-019), dan staat daar het aantal boten per bootsoort: de gegevens die later worden teruggeschreven.
- Gegeven een token met het recht `bootaantallen:lezen`, wanneer het `GET /api/v1/bootaantallen` aanroept, dan levert de API voor elk lid elke bootsoort met het aantal, ook 0, en dezelfde aantallen als de lijst per lid. Er tellen alleen boten met een toegewezen plaats; clubboten tellen niet mee (besluit 2026-10-31).
- Gegeven een lid met één boot op een plaats en één boot op de wachtlijst, wanneer de API de bootaantallen levert, dan telt alleen de boot op de plaats.
- Gegeven een clubboot op een clubplaats, wanneer de API de bootaantallen levert, dan staat die boot er niet in. De applicatie kent geen prijzen; de afrekening per bootsoort gebeurt in de ledenadministratie.
- Gegeven een token zonder het recht `bootaantallen:lezen`, wanneer het `GET /api/v1/bootaantallen` aanroept, dan weigert de API met 403.
- Gegeven de webinterface, wanneer de beheerder de instellingen opent, dan is er geen instelling voor terugschrijven.

#### BLB-039 Integratiecontainer voor imports en exports

Prioriteit: Must. Bron: intake (besluiten 2026-10-31), ADR-004, ADR-012. Afhankelijk van: BLB-029, BLB-031. Slice 6.

Als beheerder wil ik dat een aparte container de leden ophaalt en alleen via de API met de applicatie praat, zodat de koppeling met e-boekhouden los staat van de applicatie en de API niet vanaf internet bereikbaar hoeft te zijn.

- Gegeven een standaardinstallatie, wanneer de integratiecontainer de API aanroept over het interne netwerk, dan beantwoordt de API die. De container bereikt de database en de dienst `api` niet rechtstreeks.
- Gegeven de diensten van de applicatie zelf (web, api, worker), wanneer ze draaien, dan haalt geen van hen leden op of schrijft iets naar de bron; dat doet alleen de integratiecontainer.
- Gegeven een token in het secretbestand van de installatie, wanneer de beheerder het vervangt, dan gebruikt de container bij de volgende run het nieuwe token, zonder herstart.
- Gegeven een installatie zonder token voor de container, wanneer de container draait, dan meldt hij dat in zijn log en probeert hij het na een minuut opnieuw.
- Gegeven de log van de container, wanneer een beheerder die leest, dan staan er geen tokenwaarde, inloggegevens van de bron of persoonsgegevens in.
- Gegeven een draaiende integratiecontainer, wanneer een tester de instellingen bekijkt, dan draait hij zonder root en met een alleen-lezen bestandssysteem.

#### BLB-041 Boten van leden die gaan opzeggen

Prioriteit: Should. Bron: intake (besluiten 2026-10-31), architectuur §10.2 vraag 6. Afhankelijk van: BLB-006, BLB-010. Besluit: vraag 16. Slice 6.

Als beheerder wil ik zien welke leden met een opzegdatum in de toekomst nog een boot op een plaats hebben, zodat die boten vóór de opzegdatum weg zijn.

- Gegeven een import met een lid met een opzegdatum in de toekomst, wanneer de import slaagt, dan is het lid aangemaakt of bijgewerkt en blijft het lid tot die datum.
- Gegeven een lid met een opzegdatum in de toekomst, wanneer de eerste import na die datum draait, dan is het lid oud-lid (BLB-008) en staat het niet meer in dit overzicht maar bij de plaatsen van opgezegde leden (BLB-018).
- Gegeven leden met een opzegdatum in de toekomst en een boot met een plaats, wanneer de beheerder het overzicht opent, dan staan per boot de naam van het lid, de boot, rek en code van de plaats en de opzegdatum, met de vroegste opzegdatum bovenaan.
- Gegeven een lid met een opzegdatum in de toekomst en alleen een boot zonder plaats, wanneer de beheerder het overzicht opent, dan staat die boot er niet in.
- Gegeven geen enkel lid met een opzegdatum in de toekomst en een boot met een plaats, wanneer de beheerder het overzicht opent, dan staat er dat er geen boten zijn.

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
- Gegeven een plaats die vrijkomt terwijl er een wachtlijst is, wanneer de beheerder niets doet, dan blijft de plaats vrij tot de beheerder een boot kiest. (slice 7, na BLB-013)

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
- Gegeven een boot die op de wachtlijst komt of eraf gaat, wanneer de beheerder het log van de bootmutaties of de pagina van de boot opent, dan staat die handeling daar en niet in het technische log (BLB-043, besluit 2026-11-01).

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

Prioriteit: Should. Bron: intake 6, besluit 2026-10-31 (issue #17). Afhankelijk van: BLB-016. Besluit: vraag 8 en 11.

Als beheerder wil ik de huidige indeling naar Excel exporteren zodat ik die buiten de applicatie kan gebruiken.

- Gegeven de indeling, wanneer de beheerder de export start, dan komt er een Excel-bestand met een rij per plaats met rek, code, status, bootsoort, bootnaam, naam van de eigenaar en lidnummer (besluit vraag 8; de kolommen kunnen later veranderen).
- Gegeven het bestand, wanneer de beheerder het opent, dan bevat het geen adres, telefoonnummer, e-mailadres of foto.
- Gegeven een vrije plaats die geschikt is voor kajak en surfski, wanneer de beheerder exporteert, dan staat in de kolom Bootsoort "(geschikt voor Kajak, Surfski)", met de namen zoals ingevoerd (besluit vraag 11; spelling besloten 2026-10-31). Voor een clubplaats zonder boot zie vraag 19. (slice 4)

#### BLB-018 Plaatsen van opgezegde leden

Prioriteit: Must. Bron: intake 9. Afhankelijk van: BLB-008.

Als beheerder wil ik een overzicht van toegewezen plaatsen van leden die hebben opgezegd zodat ik die plaatsen kan opvolgen en vrijgeven.

- Gegeven oud-leden met een toegewezen plaats, wanneer de beheerder het overzicht opent, dan staan per plaats rek, code, boot, naam van het oud-lid en opzegdatum in de lijst, met de oudste opzegging bovenaan. Voor een lid dat zonder opzegdatum uit de bron verdween, is de opzegdatum de datum waarop de import het lid niet meer vond (besluit vraag 13).
- Gegeven een plaats in dit overzicht, wanneer de beheerder erop kiest, dan kan die de plaats vrijgeven (BLB-011).

#### BLB-019 Lijst per lid

Prioriteit: Must. Bron: intake 10. Afhankelijk van: BLB-010.

Als beheerder wil ik per lid een lijst van de boten in de loods en hun plaats zodat ik een vraag van een lid direct kan beantwoorden.

- Gegeven een lid met twee boten, waarvan één met een plaats, wanneer de beheerder de lijst opent, dan staan beide boten erin, met bootsoort en plaats of de vermelding dat er geen plaats is, en of de boot op de wachtlijst staat. (deel wachtlijst: slice 7, na BLB-013)
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

#### BLB-038 Inlogmethode toevoegen of intrekken

Prioriteit: Must. Bron: intake (besluiten architectuurvragen), ADR-001, issue #2. Afhankelijk van: BLB-022. Vragen 9 en 10: besloten in ADR-001.

Als beheerder wil ik in mijn profiel een inlogmethode toevoegen of intrekken, zodat ik een passkey naast mijn wachtwoord met TOTP gebruik, of omgekeerd. Wachtwoord en TOTP zijn samen één methode.

- Gegeven een beheerder met een wachtwoord en TOTP, wanneer die een passkey toevoegt, dan kan die daarna met de passkey inloggen.
- Gegeven een beheerder met alleen een passkey, wanneer die een wachtwoord met TOTP instelt, dan werkt de methode pas na één juiste TOTP-code.
- Gegeven een beheerder met twee methodes, wanneer die er een intrekt, dan werkt de ingetrokken methode niet meer en de andere wel.
- Gegeven een beheerder met één methode, wanneer die deze wil intrekken, dan weigert de applicatie.
- Gegeven een beheerder met beide methodes van wie het wachtwoord na vijf mislukte pogingen is vergrendeld, wanneer die binnen 15 minuten met de passkey inlogt, dan slaagt de inlog.
- Gegeven een toegevoegde of ingetrokken methode, wanneer de beheerder het log bekijkt, dan staat de wijziging erin, zonder wachtwoord of geheim.
- Gegeven een beheerder die langer dan 10 minuten geleden inlogde, wanneer die een methode toevoegt of intrekt, dan stuurt de applicatie hem eerst naar het inlogscherm (ADR-001).
- Gegeven een beheerder die een methode intrekt, wanneer de intrekking is opgeslagen, dan eindigen al zijn sessies, ook de huidige (ADR-001).

### EP-08 Mutatielog en bewaartermijn

#### BLB-024 Elke mutatie loggen

Prioriteit: Must. Bron: intake (logging), overlay §5. Afhankelijk van: BLB-022.

Als beheerder wil ik dat elke wijziging wordt vastgelegd zodat ik kan nagaan hoe een situatie is ontstaan.

- Gegeven een wijziging (aanmaken, wijzigen, verwijderen, toewijzen, vrijgeven, wachtlijst, naam en kleuren, accounts, tokens), wanneer die slaagt, dan staat er een logregel met tijdstip, wie of wat de wijziging deed, wat er veranderde en waar relevant de oude en nieuwe waarde.
- Gegeven een geslaagde import via `PUT /api/v1/leden` die een lid wijzigt, wanneer de beheerder het log bekijkt, dan staat er geen regel over dat lid; een mutatie in de botenadministratie die de import veroorzaakt, staat er wel, met de naam van het robottoken als actor (besluit 2026-10-31, vraag 20). (slice 6)
- Gegeven het log, wanneer een beheerder een regel wil wijzigen of verwijderen, dan kan dat in de applicatie niet.
- Gegeven het log, wanneer een beheerder het bekijkt, dan staan er geen wachtwoorden, tokenwaarden, adressen, telefoonnummers of e-mailadressen in.

#### BLB-025 Log onder elk overzicht

Prioriteit: Must. Bron: intake (logging), overlay §5. Afhankelijk van: BLB-024.

Als beheerder wil ik onder elk overzicht het log met de bijbehorende mutaties zien zodat ik meteen zie wat er is gewijzigd.

- Gegeven een overzicht of detailscherm voor beheerders, wanneer de beheerder het opent, dan staat onder het scherm het log met de mutaties die erbij horen, de nieuwste bovenaan. Regels uit het technische log staan alleen onder de eigen menuoptie (BLB-043, besluit 2026-11-01).
- Gegeven een plaats waaraan een boot is toegewezen of waarvan een boot is vrijgegeven, wanneer de beheerder het detail van die plaats opent, dan staat die mutatie in het log onder het detail. Een wijziging van de plaats zelf (code, bootsoorten, clubplaats) staat in het technische log (BLB-043).
- Gegeven de openbare pagina, wanneer een bezoeker die opent, dan staat daar geen log.

#### BLB-043 Twee logs: bootmutaties en techniek

Prioriteit: Should. Bron: stakeholder 2026-11-01, intake (Twee logs). Afhankelijk van: BLB-024, BLB-025. Wijzigt: BLB-025 voor het technische log.

Als beheerder wil ik het log van de bootmutaties los zien van het technische log zodat ik snel vind wat er met de boten in de loods is gebeurd.

- Gegeven het log, wanneer de beheerder het log van de bootmutaties opent, dan staan daar alleen mutaties van boten en hun plaats: een boot aangemaakt, gewijzigd of verwijderd, een foto vervangen, een plaats toegewezen of vrijgegeven, een boot op de wachtlijst gezet of eraf gehaald (besluit 2026-11-01).
- Gegeven het log, wanneer de beheerder het technische log opent via de eigen menuoptie, dan staan daar de overige regels: tokens, geweigerde API-aanroepen, beheerders en inlogmethodes, instellingen, importverzoeken en wijzigingen in de indeling (rekken en plaatsen aanmaken, wijzigen of verwijderen).
- Gegeven een boot, wanneer de beheerder de pagina van die boot opent, dan staan daaronder de logregels over die boot.
- Gegeven een lid, wanneer de beheerder de pagina van dat lid opent, dan staan daaronder de bootmutaties over de boten van dat lid.
- Gegeven een plaats, wanneer de beheerder de pagina van die plaats opent, dan staan daaronder de bootmutaties op die plaats (toegewezen, vrijgegeven).
- Gegeven `/indeling`, wanneer de beheerder die opent, dan staat daaronder geen log.
- Gegeven het menu, wanneer de beheerder `/log` opent, dan ziet die het log van de bootmutaties; het technische log heeft een eigen menuoptie ernaast.
- Gegeven een overzicht, wanneer de beheerder het opent, dan staan daaronder geen regels uit het technische log.
- Gegeven een nieuwe soort logregel, wanneer die wordt toegevoegd, dan hoort die bij precies één van beide logs; een test faalt als een soort bij geen of bij beide hoort.
- Gegeven elke beheerder, wanneer die een van beide logs opent, dan ziet die het hele log.
- Gegeven beide logs, dan gelden de regels van BLB-024 (niet te wijzigen, geen persoonsgegevens of geheimen) en BLB-026 (bewaartermijn) voor beide.

#### BLB-026 Bewaartermijn van 5 jaar

Prioriteit: Must. Bron: besluit privacy en bewaren, besluiten 2026-10-30, overlay §5. Afhankelijk van: BLB-008, BLB-024. Besluit: vraag 7.

Als beheerder wil ik dat gegevens van oud-leden en het mutatielog na 5 jaar worden verwijderd zodat de vereniging de afgesproken bewaartermijn naleeft.

- Gegeven een oud-lid dat langer dan 5 jaar geleden opzegde en van wie geen boot nog een plaats heeft, wanneer de opschoning draait, dan zijn de persoonsgegevens van dat oud-lid verwijderd, met zijn boten en foto's (besluit 2026-10-30). Een boot zonder plaats houdt het opschonen niet tegen.
- Gegeven een oud-lid dat nog een toegewezen plaats heeft, wanneer de opschoning draait, dan blijven de gegevens staan.
- Gegeven een logregel ouder dan 5 jaar, wanneer de opschoning draait, dan is de regel verwijderd.
- Gegeven een lid dat geen oud-lid is, wanneer de opschoning draait, dan blijven de gegevens altijd staan.
- Gegeven een uitgevoerde opschoning, wanneer een beheerder de technische status opent, dan staan daar het tijdstip en de aantallen verwijderde gegevens, zonder persoonsgegevens.

### EP-09 Configuratie

#### BLB-027 Naam en kleuren instellen, logo uit de installatie

Prioriteit: Must. Bron: intake (aanleiding, techniek), besluit inrichting, besluit 2026-10-31 (issue #17), ADR-008, ADR-009. Afhankelijk van: BLB-022. Besluit: vraag 12.

Als beheerder wil ik de naam van de vereniging en de kleuren instellen, en het logo uit de installatie zien, zodat de applicatie eruitziet als die van onze vereniging.

Naam en kleuren zijn gebouwd in slice 3. Het logo komt sinds 2026-10-31 uit de installatie; die criteria horen bij slice 4.

- Gegeven een ingelogde beheerder, wanneer die naam en kleuren opslaat, dan tonen alle pagina's, ook de openbare pagina en de kaartjes, de nieuwe naam en kleuren. (deel kaartjes: slice 8, met BLB-021)
- Gegeven een geldig logobestand (JPEG, PNG of WebP) op de plek die de installatie aanwijst, wanneer `web` start, dan tonen alle pagina's en de kaartjes dat logo, zonder metadata uit het bestand. Een nieuw logo verschijnt na een herstart van `web`, en er komt geen logregel. (slice 4; deel kaartjes: slice 8, met BLB-021)
- Gegeven een ontbrekend of ongeldig logobestand, wanneer `web` start, dan tonen de pagina's alleen de naam en staat de melding in de containerlog. (slice 4)
- Gegeven een ingelogde beheerder, wanneer die de instellingen opent, dan is er geen mogelijkheid om een logo te uploaden of te verwijderen. (slice 4)
- Gegeven een installatie met een logo dat in slice 3 is geüpload, wanneer de migratie van slice 4 draait, dan is dat logo uit de applicatie verwijderd en geldt alleen het logo uit de installatie. (slice 4)
- Gegeven een kleurkeuze waarbij tekst slecht leesbaar wordt, wanneer de beheerder opslaat, dan waarschuwt de applicatie.
- Gegeven een installatie zonder instellingen en zonder logobestand, wanneer iemand de applicatie opent, dan staat er een neutrale standaardnaam en een neutrale stijl.

#### BLB-028 Bootsoorten beheren

Prioriteit: Could. Bron: afleiding uit hergebruik door andere verenigingen. Afhankelijk van: BLB-002.

Als beheerder wil ik de lijst met bootsoorten aanpassen zodat een andere vereniging haar eigen soorten gebruikt.

- Gegeven de standaardlijst (kajak, Canadese kano, surfski, C11, supboard), wanneer de beheerder een soort toevoegt, dan is die soort te kiezen bij boten en plaatsen en heeft die een eigen wachtlijst.
- Gegeven een bootsoort waarvoor boten of plaatsen bestaan, wanneer de beheerder de soort wil verwijderen, dan weigert de applicatie.

### EP-10 API

De API is sinds 2026-10-31 niet meer alleen-lezen en staat standaard aan, alleen bereikbaar over het interne netwerk (intake, ADR-012). De stakeholder besloot op 2026-10-31 dat de API per installatie bewust van buiten bereikbaar mag worden gemaakt en dat persoonlijke tokens daarom blijven (vraag 15). De criteria met "(slice 10)" horen daarbij.

#### BLB-029 API aan en uit zetten

Prioriteit: Must. Bron: besluit externe API, besluiten 2026-10-30 en 2026-10-31, overlay §6, ADR-009, ADR-012. Afhankelijk van: BLB-022.

Als beheerder wil ik dat de API in de installatie aan en uit gezet kan worden zodat een vereniging zonder koppeling hem kan uitzetten.

- Gegeven een nieuwe installatie zonder waarde voor de schakelaar, wanneer over het interne netwerk een aanroep met een geldig token en voldoende rechten binnenkomt, dan beantwoordt de API die, want de API staat standaard aan (besluit 2026-10-31).
- Gegeven een installatie waarin de API via de omgeving is uitgezet, wanneer een aanroep met een geldig token binnenkomt, dan weigert de applicatie die.
- Gegeven een installatie, wanneer een beheerder de applicatie bekijkt, dan is er geen scherm om de API aan of uit te zetten.
- Gegeven een standaardinstallatie, wanneer iemand vanaf internet een aanroep naar `/api/v1/` doet, dan kent de publieke server die route niet en antwoordt hij niet met de API (ADR-012).

#### BLB-030 Persoonlijk token maken

Prioriteit: Should. Bron: besluit externe API. Afhankelijk van: BLB-029, BLB-032, BLB-042. Besluit: vraag 15. Alle criteria: slice 10.

Als beheerder wil ik een persoonlijk token maken zodat ik de API kan gebruiken zonder mijn wachtwoord te delen.

- Gegeven een ingelogde beheerder, wanneer die een token maakt met een naam, een geldigheidsduur en rechten, dan toont de applicatie de tokenwaarde één keer en daarna nooit meer.
- Gegeven een geldigheidsduur langer dan 3 jaar, wanneer de beheerder opslaat, dan weigert de applicatie.
- Gegeven een beheerder wiens account wordt geblokkeerd of verwijderd, wanneer er een aanroep met diens persoonlijke token binnenkomt, dan weigert de applicatie.

#### BLB-031 Robottoken maken

Prioriteit: Must. Bron: besluit externe API, besluiten 2026-10-31, ADR-005, ADR-012. Afhankelijk van: BLB-029, BLB-032. Besluit: vraag 1 en 5.

Als beheerder wil ik een robottoken maken dat niet aan een persoon hangt zodat koppelingen blijven werken als een beheerder vertrekt.

- Gegeven iemand met toegang tot de server, wanneer die met de CLI een robottoken maakt met naam en rechten, dan toont de CLI de tokenwaarde één keer en staat er een logregel met actor `cli`, zonder tokenwaarde. (slice 5)
- Gegeven een robottoken dat met de CLI is gemaakt zonder whitelist en zonder geldigheidsduur, wanneer de beheerder `GET /api/v1/ik` aanroept, dan is de whitelist het interne netwerk van de integratiecontainer (`KOPPELNET`) en verloopt het token na 365 dagen. (slice 5)
- Gegeven een geldigheidsduur boven 3 jaar, wanneer het token wordt gemaakt, dan weigert de CLI. (slice 5)
- Gegeven een ingelogde beheerder, wanneer die in de webinterface een robottoken maakt met naam, geldigheidsduur, rechten en IP-whitelist, dan toont de applicatie de tokenwaarde één keer. (slice 10)
- Gegeven een robottoken, wanneer de beheerder die het in de webinterface maakte wordt verwijderd, dan blijft het token werken tot het verloopt of wordt ingetrokken. (slice 10)

#### BLB-032 Rechten per token

Prioriteit: Must. Bron: besluit externe API, besluiten 2026-10-31, overlay §6, ADR-005. Afhankelijk van: BLB-029. Besluit: vraag 2, vervangen op 2026-10-31.

Als beheerder wil ik per token instellen welke rechten het heeft zodat een koppeling niet meer kan dan nodig is.

- Gegeven het aanmaken van een token, wanneer er geen enkel recht is gekozen, dan weigert de applicatie of de CLI. (slice 5)
- Gegeven een token zonder het recht `leden:importeren`, wanneer het `PUT /api/v1/leden` aanroept, dan weigert de API met 403 en verandert er niets. (slice 6)
- Gegeven een token zonder het recht op persoonsgegevens, wanneer het een boot met eigenaar opvraagt, dan staan daar naam en lidnummer maar geen adres, telefoonnummer of e-mailadres. (slice 10)
- Gegeven een bestaand token, wanneer de beheerder de rechten wijzigt, dan gelden de nieuwe rechten vanaf de volgende aanroep en staat de wijziging in het log. (slice 10)

#### BLB-033 IP-whitelist per token

Prioriteit: Must. Bron: besluit externe API, overlay §6, ADR-005. Afhankelijk van: BLB-031. Besluit: vraag 5.

Als beheerder wil ik per token vastleggen vanaf welke IP-adressen het gebruikt mag worden zodat een gestolen token weinig waard is.

- Gegeven een token met een whitelist, wanneer een aanroep vanaf een adres in de lijst komt, dan beantwoordt de applicatie die, ook voor IPv6-adressen.
- Gegeven een token met een whitelist, wanneer een aanroep vanaf een adres buiten de lijst komt, dan weigert de applicatie ook met een geldig token en komt de poging in het log.
- Gegeven een adres dat geen geldig IPv4- of IPv6-adres of -reeks is, wanneer het als whitelist wordt opgegeven, dan weigert de applicatie of de CLI het token.

#### BLB-034 Aanroepen volgen dezelfde regels als de webinterface

Prioriteit: Must. Bron: overlay §6, besluiten 2026-10-31, ADR-005, ADR-012. Afhankelijk van: BLB-029, BLB-032; het derde criterium ook van BLB-006.

Als beheerder wil ik dat de API dezelfde bedrijfsregels afdwingt, beperkt wordt en wordt gelogd zodat de API geen omweg is.

- Gegeven een aanroep zonder token of met een ongeldig token, wanneer die binnenkomt, dan weigert de applicatie. (slice 5)
- Gegeven een token zonder het recht op persoonsgegevens, wanneer het leden opvraagt, dan levert de applicatie geen adres, telefoonnummer of e-mailadres, net als de webinterface die gegevens alleen aan beheerders toont. (slice 10)
- Gegeven een import via `PUT /api/v1/leden` met minder dan de helft van het huidige aantal actieve leden, wanneer die binnenkomt, dan weigert de API met 409 en verandert er niets: de import volgt dezelfde regels als elke import (architectuur §10.1). De API kent geen andere schrijfaanroepen. (slice 6)
- Gegeven meer dan 60 aanroepen van één token binnen een minuut, wanneer de grens wordt overschreden, dan antwoordt de API met 429 en meldt wanneer het token weer mag. (slice 5)
- Gegeven een geweigerde aanroep, wanneer die is afgehandeld, dan staan token (als dat bekend is), tijdstip en reden in het log, zonder tokenwaarde. Een geslaagde aanroep komt niet in het log (besluit 2026-10-31, vraag 20). (slice 5)
- Gegeven de beschrijving van de API in de repository, wanneer een beheerder die opent, dan staan alle beschikbare aanroepen erin met recht, argumenten en antwoord. (slice 5, bijgewerkt in elke slice die een aanroep toevoegt)

#### BLB-035 Tokens overzien en intrekken

Prioriteit: Should. Bron: besluit externe API. Afhankelijk van: BLB-031. Alle criteria: slice 10.

Als beheerder wil ik alle tokens zien en intrekken zodat een lek of een vertrek snel te dichten is.

- Gegeven bestaande tokens, wanneer de beheerder het overzicht opent, dan staan per token naam, soort (persoonlijk of robot), eigenaar, rechten, vervaldatum en laatste gebruik, maar nooit de waarde.
- Gegeven drie beheerders met gelijke rechten, wanneer één beheerder een token van een ander intrekt, dan lukt dat en staat het in het log.

#### BLB-040 Beheerdocumentatie voor de integratiecontainer

Prioriteit: Must. Bron: intake (besluiten 2026-10-31), ADR-012. Afhankelijk van: BLB-031, BLB-039. Slice 6.

Als beheerder van een installatie wil ik een beschrijving van hoe de integratiecontainer zich bij de API aanmeldt, met voorbeeldcode, zodat ik het token kan instellen en een andere vereniging een eigen container kan bouwen.

- Gegeven de beheerdocumentatie, wanneer een beheerder die opent, dan staan erin: hoe je met de CLI een robottoken maakt met alleen de rechten `leden:importeren` en `bootaantallen:lezen`, hoe je het in de installatie zet, hoe je het vernieuwt, de aanroepen die de container gebruikt met voorbeeldcode (in slice 6 vier; `GET /api/v1/bootaantallen` volgt met BLB-009 in slice 9), en wat een eigen container moet doen.
- Gegeven een schone installatie, wanneer een tester alleen de stappen uit de documentatie volgt, dan slaagt een import met de stub.
- Gegeven de voorbeeldcode, wanneer een tester die uitvoert tegen een testinstallatie, dan werkt elke aanroep zoals beschreven.
- Gegeven de documentatie, wanneer een lezer die doorzoekt, dan staat er geen echte tokenwaarde of echt wachtwoord in; voorbeelden zijn herkenbaar nep.

#### BLB-042 API van buiten bereikbaar maken

Prioriteit: Should. Bron: intake (besluiten 2026-10-31), architectuur §10.2 vraag 5, ADR-012. Afhankelijk van: BLB-029, BLB-033, BLB-034. Besluit: vraag 15. Slice 10.

Als beheerder van een installatie wil ik de API bewust van buiten bereikbaar kunnen maken zodat een persoonlijk token of een koppeling buiten de installatie de API kan gebruiken.

- Gegeven een standaardinstallatie, wanneer niemand iets aan de installatie toevoegt, dan is de API niet vanaf internet bereikbaar (BLB-029).
- Gegeven een installatie die de API bewust naar buiten opent volgens de beheerdocumentatie, wanneer een aanroep van buiten met een geldig token binnenkomt vanaf een adres in de whitelist, dan beantwoordt de API die.
- Gegeven een opengezette API, wanneer een aanroep van buiten binnenkomt vanaf een adres buiten de whitelist van het token, dan weigert de API die, net als op het interne netwerk.
- Gegeven een opengezette API, wanneer een client zelf een adres in een header meestuurt, dan telt voor de whitelist alleen het adres dat de proxy van de installatie vaststelt.
- Gegeven een opengezette API, wanneer één token te veel aanroepen doet, dan geldt dezelfde grens als in BLB-034.

### EP-11 Bewaking van de installatie

#### BLB-036 Health endpoints

Prioriteit: Must. Bron: overlay §6. Afhankelijk van: geen.

Als beheerder wil ik dat de applicatie aangeeft of ze leeft en gereed is zodat een storing snel opvalt.

- Gegeven een draaiende applicatie, wanneer iemand het levend-signaal opvraagt, dan antwoordt de applicatie zonder inloggen en zonder gegevens over leden of boten.
- Gegeven een onbereikbare database, wanneer iemand het gereed-signaal opvraagt, dan meldt de applicatie dat ze niet gereed is.

#### BLB-037 Technische statuspagina

Prioriteit: Should. Bron: overlay §6, besluiten 2026-10-31, ADR-010, ADR-012. Afhankelijk van: BLB-022, BLB-006, BLB-026, BLB-039.

Als beheerder wil ik een technische statuspagina zodat ik de toestand van de installatie kan beoordelen.

- Gegeven een ingelogde beheerder, wanneer die de pagina opent, dan ziet die in leesbare vorm en als JSON de applicatieversie, de databasestatus, de laatste import van leden met resultaat en aantallen, de laatste opschoning, of de API aan of uit staat, de laatste aanroep per robottoken en wanneer de bootaantallen voor het laatst zijn opgehaald.
- Gegeven een mislukte import, wanneer de beheerder de pagina opent, dan staat de reden uit de vaste lijst erop (BLB-006), zonder tekst van buiten en zonder inloggegevens van de bron.
- Gegeven een laatste geslaagde import van meer dan 26 uur geleden, wanneer de beheerder de pagina opent, dan staat er een waarschuwing. Zo valt ook een integratiecontainer op die niet draait.
- Gegeven de statuspagina, wanneer de beheerder die bekijkt, dan staan er geen tokens, wachtwoorden of gegevens van leden op.
- Gegeven een persoonlijk token of robottoken dat binnen een maand verloopt, wanneer de beheerder de pagina opent, dan staat er een waarschuwing met de naam van het token en de vervaldatum, zonder de tokenwaarde. (slice 10 volgens architectuur §7.1; zie vraag 18)

## 5. Volgorde van slices

Slice 1 tot en met 3 zijn af. De besluiten van 2026-10-31 halen de API naar voren: zonder API werkt de import van leden niet meer. De volgorde vanaf slice 4 volgt architectuur §7.1; de letter staat in de kolom "Architectuur". Een story die over meer slices loopt, noemt per criterium de slice.

| Slice | Architectuur | Stories en criteria | Doel |
|-------|--------------|---------------------|------|
| 1 | | BLB-022, 001, 007, 006, 005, 010, 012, 020, 024, 025 | Af. Een beheerder logt in, legt een rek, een plaats en een boot van een lid vast, wijst de plaats toe, en een bezoeker ziet de openbare pagina, met een log |
| 2 | | BLB-002, 003, 004, 008, 011, 023, 038, 036 | Af. De indeling is volledig te beheren, plaatsen zijn vrij te geven, oud-leden worden herkend, meerdere beheerders werken samen en elke beheerder beheert zijn eigen inlogmethodes |
| 3 | | BLB-015, 016, 019, 018, 017, 027 | Af. De beheerder overziet de loods, exporteert naar Excel en stelt naam en kleuren in |
| 4 | A | BLB-027 criteria 2 tot en met 5, BLB-017 criterium 3 | Het logo komt uit de installatie en de export toont "(geschikt voor …)" bij een vrije plaats; sluit issue #17 |
| 5 | B | BLB-029; BLB-031 criteria 1 tot en met 3; BLB-032 criterium 1; BLB-033; BLB-034 criteria 1, 4, 5 en 6 | De API draait als eigen dienst op het interne netwerk, met een robottoken uit de CLI (maken en intrekken), controle per aanroep, rate limit en log |
| 6 | C | BLB-039, 040, 041; BLB-006, 007; BLB-008 criteria 1, 2, 4 en 5; BLB-024 criterium 2; BLB-032 criterium 2; BLB-034 criterium 3 | De integratiecontainer haalt leden op via de API en de synchronisatie in de applicatie verdwijnt; BLB-006, 007 en 008 zijn opnieuw groen via de nieuwe route |
| 7 | D | BLB-013, 014; BLB-008 criterium 3; BLB-011 criterium 3; BLB-019 criterium 1, deel wachtlijst | Boten wachten per bootsoort en de beheerder kiest zelf de plaats |
| 8 | E | BLB-021; BLB-027 criteria 1 en 2, deel kaartjes | Elke plaats krijgt een printbaar kaartje met QR-code en logo |
| 9 | F | BLB-026; BLB-037 criteria 1 tot en met 5; BLB-009 | De bewaartermijn werkt, de installatie is te bewaken en de bootaantallen staan klaar, terugschrijven staat uit |
| 10 | G | BLB-030, 035, 042; BLB-031 criteria 4 en 5; BLB-032 criteria 3 en 4; BLB-034 criterium 2 | Leesendpoints, persoonlijke tokens, tokenschermen, en de keuze om de API van buiten bereikbaar te maken |
| 11 | H | BLB-028 | Een andere vereniging past de bootsoorten aan |

Slice 5 gaat vóór slice 6, omdat de integratiecontainer het contract en het robottoken uit slice 5 nodig heeft. Slice 6 gaat vóór de wachtlijst, zodat BLB-008 criterium 3 meteen op de definitieve importroute wordt gebouwd. Slice 4 staat los van de API.

### Verschoven criteria

| Criterium | Naar slice | Wacht op | Criteria die van dezelfde latere story afhangen |
|-----------|-----------|----------|-------------------------------------------------|
| BLB-008 criterium 3 (boot van oud-lid van de wachtlijst) | 7 | BLB-013 | BLB-011 criterium 3, BLB-019 criterium 1 (deel wachtlijst), BLB-014 |
| BLB-011 criterium 3 en BLB-019 criterium 1, deel wachtlijst | 7 | BLB-013 | BLB-008 criterium 3 |
| BLB-027 criteria 1 en 2, deel kaartjes | 8 | BLB-021 | Geen andere |
| BLB-006, BLB-007, BLB-008 criteria 1, 2, 4 en 5 (opnieuw groen) | 6 | BLB-039 | BLB-024 criterium 2, BLB-032 criterium 2, BLB-034 criterium 3, BLB-040 |
| BLB-034 criterium 3 (veiligheidsgrens via `PUT /api/v1/leden`) | 6 | BLB-006 | BLB-024 criterium 2, BLB-032 criterium 2 |
| BLB-031 criteria 4 en 5, BLB-032 criteria 3 en 4, BLB-034 criterium 2 | 10 | Tokenschermen en leesendpoints van slice 10 | BLB-030, BLB-035, BLB-042 |

Het log uit slice 1 bevat vanaf het begin de datum van elke mutatie, zodat opschonen in slice 9 mogelijk is.

## 6. Won't Have in deze cyclus

| Onderwerp | Reden |
|-----------|-------|
| Import van de bestaande spreadsheet | Besluit stakeholder: volgt later |
| Daadwerkelijk terugschrijven naar e-boekhouden | Alleen voorbereid (BLB-009) |
| Leden aanmaken of wijzigen in de webinterface | De ledenbron is leidend; alleen de import via de API werkt leden bij |
| Logo uploaden of verwijderen in de applicatie | Besluit stakeholder 2026-10-31: het logo staat in de installatie |
| Meerdere verenigingen in één installatie | Besluit stakeholder: één vereniging per installatie |
| Automatische toewijzing van plaatsen | Besluit stakeholder: de beheerder kiest zelf |
| Aparte rol voor systeembeheer | Besluit stakeholder: drie gelijke beheerders |

## 7. Besluiten op de open vragen

De stakeholder heeft deze vragen op 2026-10-30 besloten. Ze staan ook in `docs/business/intake.md`.

| Nr | Vraag | Besluit | Raakt |
|----|-------|---------|-------|
| 1 | Wat is de maximale geldigheid van een robottoken? | 3 jaar. Een token zonder einddatum is niet toegestaan. Een token dat binnen een maand verloopt, geeft een waarschuwing op de technische statuspagina. | BLB-031, BLB-037 |
| 2 | Welke functies biedt de API in de eerste versie, en welke rechten zijn er per token? | Eerst alleen lezen: plaatsen, boten, leden, wachtlijst, met een apart recht voor persoonsgegevens. Schrijven volgt in een latere story. Vervangen op 2026-10-31: de import van leden schrijft via de API (vraag 14 hieronder). | BLB-032, BLB-034 |
| 3 | Moet de instemming per lid worden vastgelegd? | Nee. Alle leden hebben ingestemd met het openbaar tonen van hun naam en de foto van hun boot. | BLB-020, BLB-021 |
| 4 | Telt de volgorde op de wachtlijst mee? | Nee. De wachttijd is informatie; de beheerder kiest vrij en de applicatie legt geen reden vast. | BLB-013, BLB-014 |
| 5 | Is een IP-whitelist verplicht? | Verplicht bij een robottoken, optioneel bij een persoonlijk token. Een lege lijst bij een robottoken weigert de applicatie. | BLB-031, BLB-033 |
| 6 | Hoe vaak synchroniseren we met de ledenbron? | Dagelijks, en handmatig te starten. Een verdwenen lid wordt oud-lid en wordt niet verwijderd. Sinds 2026-10-31 doet de integratiecontainer de import. | BLB-006, BLB-008 |
| 7 | Wanneer begint de termijn van 5 jaar? | Voor een oud-lid op de opzegdatum, maar niet zolang het oud-lid nog een boot of plaats in de loods heeft. Voor het log vanaf de mutatie. Verfijnd op 2026-10-30: alleen een boot met een plaats houdt het opschonen tegen; boten en foto's gaan mee. | BLB-026 |
| 8 | Welke kolommen staan in de Excel-export? | Rek, code, status, bootsoort, bootnaam, naam van de eigenaar en lidnummer. Geen adres, telefoonnummer, e-mailadres of foto. De kolommen kunnen later veranderen. | BLB-017 |

### Vragen besloten door foundation

Foundation besloot deze vragen op 2026-10-30 in ADR-001 v1.1.0. Aegis toetst de uitwerking bij de review van BLB-038.

| Nr | Vraag | Besluit | Raakt |
|----|-------|---------|-------|
| 9 | Moet een beheerder zich opnieuw bewijzen (passkey, of wachtwoord met TOTP) voordat hij een methode toevoegt of intrekt? | Ja. Toevoegen of intrekken lukt alleen als de beheerder in de afgelopen 10 minuten heeft ingelogd; anders gaat hij eerst naar het inlogscherm (ADR-001). | BLB-038 |
| 10 | Eindigen lopende sessies als een beheerder een methode intrekt? | Ja. Intrekken hoogt de sessieversie op: alle sessies van die beheerder eindigen, ook de huidige. Toevoegen laat sessies staan (ADR-001). | BLB-038 |

### Besluiten van de stakeholder (2026-10-31)

De stakeholder besloot deze vragen op 2026-10-31. Ze staan ook in `docs/business/intake.md`. Vraag 11 tot en met 13 komen uit issue #17, vraag 15 en 16 uit architectuur §10.2.

| Nr | Vraag | Besluit | Raakt |
|----|-------|---------|-------|
| 11 | Wat staat in de kolom Bootsoort van de export bij een vrije plaats? | "(geschikt voor …)", met de bootsoorten die op die plaats mogen. | BLB-017 |
| 12 | Moet een logo te verwijderen zijn? | Nee. Het logo staat in de installatie, niet in de applicatie; wijzigen wordt niet gelogd. Naam en kleuren stelt de beheerder in de applicatie in. | BLB-027, BLB-021 |
| 13 | Klopt de datum "Opgezegd op" voor een lid dat zonder opzegdatum uit de bron verdween? | Ja. De datum waarop de import het lid niet meer vond, telt als opzegdatum (besluit 2026-10-30). | BLB-018, BLB-008 |
| 14 | Hoe lopen imports en exports? | Een aparte, vervangbare container doet ze, alleen via de API over het interne netwerk. De API staat standaard aan, met het interne netwerk als whitelist, en is niet meer alleen-lezen. De beheerdocumentatie beschrijft het aanmelden met voorbeeldcode. Dit vervangt vraag 2 en de standaard "uit" van de API. | BLB-006 tot en met 009, 024, 029 tot en met 034, 037, 039, 040 |
| 15 | Vervallen persoonlijke tokens nu de API niet vanaf internet bereikbaar is? (architectuur §10.2, vraag 5) | Nee. Een installatie mag de API bewust van buiten bereikbaar maken; persoonlijke tokens blijven daarom mogelijk. | BLB-030 tot en met 035, 042 |
| 20 | Komen aanroepen van de API en wijzigingen in leden door de import in het log? | Nee. De applicatie is niet leidend voor de ledenadministratie. Geweigerde aanroepen en mutaties in de botenadministratie, ook door een import, komen wel in het log; de uitkomst van een import staat op de statuspagina. | BLB-006 tot en met 008, 024, 033, 034 |
| 16 | Mag een import leden met een opzegdatum in de toekomst aanmaken? (architectuur §10.2, vraag 6) | Ja, e-boekhouden kan dat leveren. Heeft zo'n lid boten in de loods, dan ziet de beheerder die boten met de opzegdatum, zodat ze vóór die datum weg zijn. | BLB-006, BLB-041 |

### Besluiten van apex (2026-10-31)

- BLB-029, 031, 032, 033 en 034 gaan van Should naar Must. De import van leden (BLB-006, Must) werkt sinds 2026-10-31 alleen via de API en het robottoken.
- BLB-026 criterium 1 volgt nu het besluit van 2026-10-30: alleen een boot met een plaats houdt het opschonen tegen. De oude tekst ("geen plaats of boot meer in de loods") sprak dat besluit tegen.
- BLB-032 criterium 1 (een token met leesrecht wil een toewijzing maken) is vervangen door de controle op `leden:importeren`. De API kent geen schrijfaanroep voor toewijzen.
- BLB-041 (boten van leden die gaan opzeggen) is Should en hoort bij slice 6, omdat de import daar wordt gebouwd. De import werkt ook zonder dit overzicht.
- BLB-042 (API van buiten bereikbaar maken) is Should en hoort bij slice 10, net als BLB-030: een persoonlijk token is alleen nuttig als de API van buiten bereikbaar is.

### Open vragen

| Nr | Vraag | Voor | Blokkerend | Advies van apex |
|----|-------|------|------------|-----------------|
| 17 | Hoe trekt iemand het robottoken in vóór slice 10? ADR-012 beschrijft alleen het maken met de CLI. | Foundation | Ja, voor de eerste uitrol in productie; niet voor de bouw van slice 5 | Besloten door de regie: `flask token intrekken <naam>` in slice 5 (ADR-012 v1.1.0) |
| 18 | De waarschuwing voor tokens die binnen een maand verlopen (BLB-037 criterium 5) staat in architectuur §7.1 bij slice 10, maar ADR-010 zet hem op de statuspagina van slice 9. Het robottoken bestaat al vanaf slice 5 en verloopt na 365 dagen. | Regie en foundation | Nee | Besloten door de regie: slice 9, met BLB-037 (ADR-010) |
| 19 | Geldt "(geschikt voor …)" in de export ook voor een clubplaats zonder boot? Het besluit noemt alleen een vrije plaats. | Stakeholder | Nee; slice 4 bouwt het voor een vrije plaats | Besloten door de stakeholder 2026-10-31: ja, ook voor een clubplaats zonder boot |
| 21 | BLB-040 vraagt de vijf aanroepen van de container met voorbeeldcode, maar `GET /api/v1/bootaantallen` hoort bij BLB-009 in slice 9. Slice 6 beschrijft vier aanroepen en noemt de vijfde voor slice 9 (issue #22). Blijft dat zo, of gaat de aanroep naar voren? | Apex en foundation | Nee; de container gebruikt de aanroep pas als terugschrijven aan kan | Besloten door foundation: zo laten, zoals forge adviseerde. Het contract in ADR-012 v1.3.0 kent vijf aanroepen; slice 6 bouwt er vier. BLB-040 criterium 1 en 3 gelden in slice 9 ook voor de vijfde aanroep |

## 8. Aannames

- Een plaats heeft ten hoogste één boot, en een boot heeft ten hoogste één plaats. Verplaatsen is vrijgeven gevolgd door toewijzen.
- Een plaats blijft toegewezen na opzegging van het lid tot de beheerder haar vrijgeeft. De applicatie geeft niet automatisch vrij.
- Een boot heeft hooguit één foto. De toegestane bestandsgrootte en bestandstypen bepaalt foundation.
- De vijf bootsoorten uit de intake zijn de startlijst. Aanpassen is BLB-028.
- Besluit stakeholder 2026-10-30: de API gaat aan en uit in de installatie, via een omgevingsvariabele (ADR-009), niet in de applicatie. Sinds 2026-10-31 staat hij standaard aan.
- Een IP-whitelist bevat adressen en adresreeksen, zowel IPv4 als IPv6.
- Een wachttijd telt vanaf de dag van aanmelding op de wachtlijst.
