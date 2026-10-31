# Terugblik forge, slice 4

**Datum:** 2026-10-31
**Taak:** slice 4 bouwen (BLB-027 criteria 2 tot en met 5, BLB-017 criterium 3), issue #18, lost #17 op.

## Wat ging goed

ADR-008 v1.1.0 beschreef het logo uit de installatie volledig: pad, standaard, gedrag bij een ontbrekend bestand en de route. Ik hoefde geen ontwerpvraag te stellen. De lokale database had nog een geüpload logo uit de E2E-run van slice 3, zodat de migratie op echte data te controleren was.

## Wat kon beter

Na `up -d` gaf Nginx een 502, omdat het nog het oude IP-adres van de nieuwe container `web` gebruikte. Een herstart van `nginx` loste dat op. Een eerste versie van de test op de grens van 10 MB liet een mutant zonder die grens overleven: de inhoud was ook ongeldig als afbeelding.

## Wat deed ik zelf goed

Ik heb de grens van 10 MB getoetst met een mutant en de test daarop aangescherpt (een geldige PNG met 10 MB aanvulling). De worker leest het logo niet, zodat zijn log geen valse melding geeft. De migratie is gecontroleerd met een eigen unittest én op de lokale database (head, downgrade, upgrade, rechten).

## Wat heb ik onderweg zelf verbeterd

De test "geen mutatie" telde eerst alle logregels, ook die van het aanmaken van een plaats; nu telt hij alleen regels over instellingen. De docstring van `huidig()` en de tekst op het instellingenscherm zeggen nu waar het logo staat.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: na een wijziging in `docker-compose.yml` of `compose.dev.yml` die `web` opnieuw aanmaakt, herstart ook `nginx` voordat je E2E-tests of curl-controles draait.

Zet in de opdracht: een test op een grens (grootte, aantal, duur) gebruikt invoer die zonder die grens geldig is, en de mutant zonder de grens moet falen.
