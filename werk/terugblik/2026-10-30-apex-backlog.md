# Terugblik Apex, productbacklog botenloodsbeheer

Datum: 2026-10-30. Taak: `docs/product/backlog.md` schrijven (37 stories, 11 epics).

## Wat ging goed

De bronvolgorde was duidelijk, dus er was geen botsing tussen intake en business outline. De omvang en de rollen stonden in de opdracht, waardoor ik geen aannames hoefde te doen over het aantal beheerders. De lijst met onderwerpen die erbij moesten (API, tokens, bewaartermijn, health) liet zich direct vertalen naar epics.

## Wat kon beter

De eerste versie telde 6431 woorden, boven het maximum van 6000. Ik schreef eerst volledig en schrapte daarna. De mix van Must, Should en Could in de samenvatting klopte bovendien niet met de stories en moest worden gecorrigeerd. Een open punt dat ik te laat zag: "in de configuratie" voor de API kan in de interface of in de installatie, en zonder systeembeheerrol is dat een echte keuze. Ik heb het als aanname vastgelegd in plaats van als vraag, omdat het maximum van 8 vragen al gevuld was.

## Wat deed ik zelf goed

Ik heb de twaalf intakestories herleidbaar gemaakt met een tabel. Bij elke story waar privacy of een bedrijfsregel speelt staat een unhappy flow. Voor de open vragen heb ik een voorstel gegeven en stories die erop wachten gemarkeerd als geblokkeerd, zodat geen story als gereed telt. De gemeenschappelijke eisen staan één keer bovenaan, wat woorden spaarde.

## Wat heb ik onderweg zelf verbeterd

Ik heb de tellingen (stories, prioriteiten, woorden) met `grep` en `wc -w` gecontroleerd en de samenvatting aangepast. Ik heb dubbele acceptatiecriteria geschrapt, vooral herhalingen van "bezoeker wordt geweigerd", die al onder de gemeenschappelijke eisen vallen. Gedachtestreepjes zijn gecontroleerd met `grep`.

## Wat kan structureel beter in de opdracht of de afspraken

- Zet in de opdracht: geef het woordbudget per onderdeel, bijvoorbeeld "stories maximaal 4500 woorden, rest 1500". Dan hoeft er achteraf niet geschrapt te worden.
- Zet in de opdracht: zeg of de keuze tussen "in de applicatie" en "in de installatie" voor instellingen bij foundation ligt, zodat Apex er geen aanname over hoeft te maken.
- Zet in de opdracht: noem welke open vragen blokkerend zijn, zodat de statuskolom van het backlog niet door Apex hoeft te worden afgeleid.
- Zet in de opdracht: laat het aantal stories per prioriteit door een script tellen en vraag niet om een handmatige samenvatting.
