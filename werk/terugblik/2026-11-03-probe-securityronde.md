# Terugblik probe, DAST-securityronde na slice 11

**Datum:** 2026-11-03
**Taak:** DAST tegen een eigen stack (web, API op koppeling, API van buiten), rapport in `werk/security/2026-11-03-probe-dast.md`

## Wat ging goed

Het voorbeeld in `schermafbeeldingen.sh` maakte een eigen stack eenvoudig: eigen projectnaam, subnet en een eigen omgevingsbestand met nieuwe geheimen, zonder de gedeelde stack te raken. De briefingregels over een container op het koppelnet en een tweede token zonder recht maakten de positieve controles op de API direct mogelijk.

## Wat kon beter

De stack leest de code via de mounts van `compose.dev.yml` uit de werkmap. Terwijl bedrock aan #58 werkte, herstartte de api drie keer door `--reload`, en wist ik niet precies welke code ik testte. De eerste ingelogde ZAP-scan en API-scan stuurden geen sessie of token mee; dat zag ik pas aan de toegangslog, na ruim tien minuten.

## Wat deed ik zelf goed

Elke weigering heb ik eerst met een geslaagde aanroep gecontroleerd. Bij PRB-01 heb ik met een echte inlog bewezen dat de omzeiling werkt, niet alleen een andere statuscode laten zien. De ZAP-runs heb ik in de toegangslog nagelopen in plaats van op het lege rapport te vertrouwen.

## Wat heb ik onderweg verbeterd

Twee ZAP-containers in hetzelfde netwerk als Traefik botsten op poort 8080; ze kregen een eigen poort. De vervanging met `${...}` in de replacer werkte niet; ik zette de waarde vast in een tijdelijk plan en wiste dat daarna. De API-scan kreeg één thread met een pauze, zodat de rate limit per token de scan niet blokkeerde.

## Wat kan structureel beter

- Zet in de opdracht: "Een DAST-stack draait zonder `compose.dev.yml`-mounts van `app/` of op een eigen worktree van de te testen commit, zodat parallel werk in de werkmap de test niet verandert."
- Zet in de opdracht: "Controleer na de eerste minuut van een ingelogde scan in de toegangslog van web of api dat de verzoeken ingelogd zijn (200 op een beschermde route), voordat je de active scan laat doorlopen."
- Zet in de opdracht: "Een proef op een rate limit van Traefik probeert ook het pad met `%2F` en andere gecodeerde tekens."
