# Terugblik forge, slice 9 (issue #48)

**Datum:** 2026-11-02 en 2026-11-03
**Taak:** bewaartermijn, technische statuspagina en bootaantallen (BLB-026, BLB-037 criteria 1 tot en met 5, BLB-009, BLB-040 criteria 1 en 3)

## Wat ging goed

De rechten lagen er al grotendeels. `botenloods_taken` mocht al DELETE op `logregel`, `lid`, `boot` en `afbeelding`, dus de migratie bleef bij twee GRANT's voor de API. Foto's staan in de database (ADR-008), waardoor er bij het opschonen geen bestanden op schijf achterblijven. De tien mutanten (opschoongrens, loggrens beide kanten, plaatscontrole, volgorde van de startdatum, één run per dag, rechtcontrole, telregel, tokenvenster, importvenster) vielen alle tien.

## Wat kon beter

Twee E2E-fouten kwamen pas tegen de echte stack aan het licht. Een view met twee routes geeft in `url_for` de route die het eerst geregistreerd is, en dat is de onderste decorator: het menu wees naar `/status.json`. En `get_by_role("columnheader")` vindt niets op een smal scherm, omdat de CSS de `thead` dan verbergt. De volledige E2E-suite kon pas na 03:00 draaien door de regel over de nachtelijke import.

## Wat deed ik zelf goed

Ik liep de kopieën na vóór het bouwen: het log toont `lid:<id>` zonder naam, de wachtlijst volgt via de cascade, de import slaat een oud record over met dezelfde `jaren_terug`-grens. Daarvoor is een test die opschoont en daarna importeert. Elke grens heeft een test aan beide kanten met de testnaam per kant.

## Wat heb ik onderweg verbeterd

`API_INGESCHAKELD` stond alleen bij `api`; `web` las dus altijd de standaard en had op de statuspagina een verkeerde stand kunnen tonen. Ik heb de variabele naar de gedeelde omgeving verplaatst. Een overbodige `where` in de telregel (een clubboot heeft geen lid en telt al niet) is eruit.

## Wat kan structureel beter

- Zet in de opdracht: "Een view met meer routes krijgt de route voor `url_for` als onderste decorator; controleer het menu-item met een unittest op de `href`."
- Zet in de opdracht: "Een E2E-selector op een tabel gebruikt geen `columnheader`; onder 40rem verbergt de CSS de `thead`."
- Zet in de opdracht: "Plan de volledige E2E-run vóór 00:00 of na `SYNC_TIJDSTIP`; een bouwopdracht die rond middernacht klaar is, wacht anders drie uur."
- Zet in de opdracht: "Een nieuwe omgevingsvariabele die meer dan één dienst leest, staat in de gedeelde omgeving van compose; controleer per dienst met `docker compose config`."
