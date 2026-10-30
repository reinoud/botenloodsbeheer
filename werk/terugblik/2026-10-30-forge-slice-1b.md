# Terugblik forge: slice 1b (indeling, boten, ledenbron en openbare pagina)

Datum: 2026-10-30. Taak: GitHub-issue #8 met de bevindingen #3, #4 en #7.

## Wat ging goed

De ADR's 003, 004 en 008 gaven genoeg detail om zonder vragen te bouwen: drie identiteiten per plaats, de stappen van de synchronisatie en de verwerking van foto's. De stack draaide al, en Pillow kwam met één `uv lock` in het lockbestand. De unitsuite (120 tests) en de E2E-suite (6 tests) slaagden zonder overgeslagen tests, en elke E2E-test slaagde ook los met `-k`.

## Wat kon beter

De migratie liet ik eerst door Alembic genereren in een alleen-lezen mount; dat kostte drie pogingen. Seed en ADR-004 botsen: §6.3 vraagt twee oud-leden met een opzegdatum van meer dan 5 jaar geleden, maar stap 4 van de synchronisatie slaat die over. De ADR ging voor. De worker in de ontwikkelstack synchroniseert direct na het starten, omdat het al na 03:00 is. Daardoor meldde `flask seed` eerst "0 leden"; die melding telt nu de leden in de database.

## Wat deed ik zelf goed

Ik zag dat een bestaand lid met een tikfout in het e-mailadres anders oud-lid zou worden: een overgeslagen record met een geldig lidnummer telt nu als gezien. Een mislukte geplande synchronisatie probeert het hooguit één keer per uur opnieuw, zodat een storing van de bron geen logregel per ronde van 15 seconden geeft. De openbare pagina krijgt alleen een dict met de toegestane velden, en de E2E-test leest adres, telefoon, e-mail en lidnummer eerst als beheerder en zoekt ze daarna in de HTML van de openbare pagina.

## Wat heb ik onderweg verbeterd

Een test riep `lid()` drie keer aan in een dict met `.get`, wat een dubbel lidnummer gaf; nu één aanroep. Het alfabet van de publieke sleutel mist ook de kleine o. De uploadgrens heb ik via Nginx nagelopen: 3 MB komt door, 11 MB krijgt 413.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Noem bij een seed of fixture welke regel voorgaat als architectuur §6.3 botst met een ADR."
Zet in de opdracht: "Geef bij een geplande taak aan hoe vaak die na een fout opnieuw mag proberen."
