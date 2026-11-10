# Terugblik probe: DAST vóór release v1.0.0

**Datum:** 2026-11-10
**Taak:** DAST op 6ee8ee9 in een eigen worktree, hertoets PRB-01 tot en met PRB-04, verslag `werk/security/2026-11-10-probe-dast.md`

## Wat ging goed

De eigen worktree met een extra compose-bestand in de scratchpad (eigen imagenaam, `volumes: !reset []`, geen databasepoort) hield de test los van de gedeelde stack en van parallel werk. De ledenimport in twee rondes uit `draai.sh` werkte direct. De ingelogde ZAP-scan bleef 20 minuten ingelogd.

## Wat kon beter

ZAP in de netwerkruimte van Traefik startte de eerste keer niet, omdat poort 8080 daar bezet is; dat kostte een ronde. De seed geeft 11 rekken en 229 plaatsen, niet de 10 en 160 uit de brief. Het hertoetsen kostte meer tijd dan nodig, omdat er geen scripts van de vorige ronde waren.

## Wat deed je zelf goed

Elke weigering heb ik met een positieve controle afgezet (clubboot op de clubplaats, passend token, geldige keuze). Bij de clubplaats zag ik dat de eerste weigering een andere oorzaak had (boot had al een plaats) en heb ik de proef met een andere boot herhaald. De ZAP-rapporten heb ik op sessies en tokens nagekeken voordat ze in de scratchpad bleven.

## Wat heb je onderweg verbeterd

De client hergebruikte een TOTP-code binnen hetzelfde tijdvenster en werd terecht geweigerd; ik heb een wachtstap op een nieuw venster ingebouwd. Een `sed -i ''` faalde omdat `sed` op deze host GNU sed is; ik ben overgestapt op python3.

## Wat kan structureel beter

Zet in de opdracht: "ZAP in de netwerkruimte van Traefik draait met `-port 8099`, want 8080 is daar bezet; bewaar de scripts van de DAST-ronde (zonder geheimen) in de scratchpad en noem hun pad in het verslag, zodat de volgende ronde kan hertoetsen zonder opnieuw te bouwen."
