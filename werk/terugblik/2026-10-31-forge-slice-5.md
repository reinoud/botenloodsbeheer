# Terugblik forge, slice 5 (issue #19)

**Datum:** 2026-10-31
**Taak:** API als eigen dienst met robottoken, controle per aanroep, rate limit en log

## Wat ging goed

De ADR's waren concreet genoeg om zonder vragen te bouwen: volgorde van de controle, tokenvorm, rechtenlijst en netwerken stonden er. De afbakening in de brief (alleen `GET /api/v1/ik`, worker ongewijzigd) hield de diff klein. Alle vier mutanten op de grenzen en controles faalden zoals bedoeld.

## Wat kon beter

Ik draaide een `git stash` terwijl de stack liep en startte in die stand een testcontainer. Compose las toen de oude compose-bestanden en maakte `db` en `api` opnieuw aan op het oude netwerk. Daarna gaf Nginx 502, tot ik de stack opnieuw opbouwde en Nginx herstartte.

## Wat deed ik zelf goed

Ik heb de bereikbaarheid in de stack zelf nagelopen vanaf drie netwerken (`koppeling`, `achterkant`, de publieke poort) en het log op tokenwaarden gecontroleerd. Daarbij vond ik dat de standaardregel uit `nginx.conf` (formaat `main`) naast `zonder_code` meeschreef. De code van een uitnodiging stond daardoor sinds slice 1 toch in de toegangslog.

## Wat heb ik onderweg verbeterd

De `access_log` staat nu per server (`app.inc`, `api.inc`, redirectserver in `prod.conf`), zodat alleen het formaat `zonder_code` schrijft. De sleutel van de rate limit is de prefix van het token in plaats van de header: core-Nginx kan niet hashen, en zo staat de tokenwaarde niet in het geheugen van Nginx. `db-init.sh` is herhaalbaar gemaakt, zodat een bestaande installatie de nieuwe rol `botenloods_api` kan krijgen.

## Wat kan structureel beter

Zet in de opdracht: "Draai geen compose-commando terwijl een `git stash` actief is; vergelijk een baseline in een aparte worktree." En: "Controleer bij elke wijziging aan Nginx met `docker compose logs nginx` dat elk verzoek precies één logregel geeft, in het formaat `zonder_code`."
