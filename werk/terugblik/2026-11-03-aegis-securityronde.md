# Terugblik aegis: statische securityronde na slice 11

**Datum:** 2026-11-03
**Taak:** statische analyse van code, afhankelijkheden en images (overlay §7), rapport `werk/security/2026-11-03-aegis-statisch.md`

## Wat ging goed

De brief noemde de ADR's met de drempels, de bekende issues en de regels voor het draaien. Ik kon daardoor direct toetsen tegen een norm en hoefde niets opnieuw te melden. De scanners draaiden in een losse container naast het lezen van de code. Dat kostte geen wachttijd.

## Wat kon beter

Trivy meldt in de images de OS-pakketten en de meegeleverde pip-pakketten in één lijst. Het scheiden van wat een oplossing heeft en wat bereikbaar is, kostte de meeste tijd. De brief noemde niet of de leesquery op de rechten in de gedeelde database mocht. Ik heb hem gedaan omdat hij alleen leest.

## Wat deed ik zelf goed

Ik heb de rechten per rol in de database gecontroleerd, naast de migraties. Zo is AEG-04 een vaststelling en geen vermoeden. Voor elke CVE heb ik nagegaan of de route bereikbaar is, bijvoorbeeld Ghostscript (niet in het image) en pyasn1 (alleen bij het registreren van een passkey).

## Wat heb ik onderweg zelf verbeterd

Ik wilde de digest van `docker/Dockerfile` als nieuwe bevinding melden. De acceptatiecriteria van #25 noemen al elke `FROM`, dus het staat nu als commentaar bij #25. De regelnummers in het rapport heb ik achteraf met grep gecontroleerd en twee verbeterd.

## Wat kan structureel beter

Zet in de opdracht: "Een leesquery op `information_schema` in de gedeelde database mag; proeven die rate limits of vergrendelingen raken niet." En: "Scan met `trivy --ignore-unfixed` en rapporteer meldingen zonder oplossing alleen als aantal."
