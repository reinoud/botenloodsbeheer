# Terugblik forge: slice 2

**Datum:** 2026-10-30
**Taak:** slice 2 bouwen (BLB-002, 003, 004, 008, 011, 023, 038 en 036), met issue #10 en de E2E-test voor issue #2. Feature-issue #11.

## Wat ging goed

De opdracht noemde de gezagsvolgorde, wat buiten de slice valt (wachtlijst) en welke regel per `FOR UPDATE`-pad geldt. ADR-001 v1.1.0 gaf de drempels (10 minuten, intrekken beëindigt alle sessies), zodat ik zonder vragen kon bouwen. De webrol had al alle rechten; er was geen migratie nodig.

## Wat kon beter

De E2E-suite liep na vier nieuwe tests vast op de rate limit van Nginx (20 direct, daarna 30 per minuut per IP-adres). Twee bestaande tests faalden daardoor, zonder fout in de code. Dat stond nergens als bekende grens.

## Wat deed ik zelf goed

Elke racetest heb ik met een mutant gecontroleerd: zonder `with_for_update` falen alle vijf. De racetests gebruiken één hulpfunctie (`tests/unit/hulp.py: race`), zodat een nieuwe vergrendeling een test van een paar regels vraagt. Bootsoorten, clubplaats en code lopen via één domeinfunctie, één formulier en één logregel.

## Wat heb ik onderweg verbeterd

Het log verborg de plaatscode bij `plaats.aangemaakt` en `plaats.verwijderd`, omdat de sleutel `code` op de lijst met geheime velden staat. De sleutel heet nu `plaatscode`. De relatie `Beheerder.passkeys` kreeg `passive_deletes`, anders brak verwijderen van een beheerder met passkeys.

## Wat kan structureel beter

Zet in de opdracht: "De rate limit op `/inloggen` en `/uitnodiging` telt alle E2E-tests samen; `tests/e2e/draai.sh` draait per bestand met 40 seconden pauze. Houd een nieuw E2E-bestand onder 20 inlogverzoeken."
Zet in de opdracht: "Een logveld met de naam `code`, `adres`, `telefoon` of `email` wordt in het log `gewijzigd`; kies een andere sleutel als de waarde zichtbaar moet zijn."
