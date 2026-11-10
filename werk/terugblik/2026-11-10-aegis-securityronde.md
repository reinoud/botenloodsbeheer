# Terugblik aegis: statische securityronde vóór v1.0.0

**Datum:** 2026-11-10
**Taak:** statische analyse van code, afhankelijkheden en images op commit 6ee8ee9, verslag in `werk/security/2026-11-10-aegis-statisch.md`

## Wat ging goed

De brief noemde de scope, de verboden acties (geen live proeven, geen suite, geen hertag) en de bestaande codes. Daardoor kon ik direct beginnen. De briefingchecklist gaf de Trivy-regel en de eis van amd64, zodat de scan gelijk is aan die van de release.

## Wat kon beter

De diff van 115 bestanden bevat veel CSS, fonts en templates. Een lijst van de securityrelevante paden in de brief had zoekwerk gescheeld. Het accepteren van de buffering van 25 MB in ADR-013 vond ik pas na een zoekopdracht; zonder die vondst was het een dubbele bevinding geworden.

## Wat deed ik zelf goed

Ik heb de images gebouwd uit een `git archive` van 6ee8ee9 in de scratchpad, zodat parallel werk in de werkmap de scan niet raakte. Elke stand van de vorige ronde heb ik in code of database nagegaan, niet uit de issuetitels.

## Wat heb ik onderweg verbeterd

Trivy fs liet de dev-afhankelijkheden standaard weg; ik heb opnieuw gescand met `--include-dev-deps`. Regelnummers in het verslag heb ik na het schrijven met grep gecontroleerd en twee verkeerde verbeterd.

## Wat kan structureel beter

Zet in de opdracht: "Scan met trivy fs altijd met `--include-dev-deps`, bouw de images uit `git archive <commit>` in de scratchpad, en zoek vóór elke nieuwe bevinding in `docs/architecture/adr/` naar een aanvaard restrisico op hetzelfde punt."
