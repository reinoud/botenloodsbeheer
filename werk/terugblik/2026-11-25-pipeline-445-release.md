# Terugblik pipeline, release-controles v2.7.0 (#445)

Datum: 2026-11-25 (run over middernacht, tot 2026-11-26)
Taak: unitsuite, trivy en release-E2E in project `pl445` op releasecommit f7ae179.

## Wat ging goed

- De volgorde uit de overlay (unit, trivy, dan E2E) werkte. Trivy was schoon, dus de E2E kon zonder omweg starten.
- Eén run, geen herhaling. `draai.sh` liep na de mislukte test door tot en met `vangnet.sh`, zodat alle vier de fasen toch een uitkomst hadden.
- Logs van traefik, api en integratie en `docker inspect` van api stonden in de scratchpad vóór `down -v`.
- De dev-stack is niet geraakt: de `StartedAt` van de dev-integratie bleef 17:01:53Z.

## Wat kon beter

- De unitsuite duurde 18 minuten. Ik heb de amd64-builds en de trivy-scans ernaast gedraaid, maar de E2E kon pas daarna starten.
- Het vangnetimage haalde ik op met `docker pull --platform linux/amd64`. Dat gaf exit 1 ("cannot overwrite digest") en liet een arm64-image achter onder de tag. Mijn eerste trivy-scan van het vangnet was dus arm64. Ik heb daarna amd64 gescand met `--image-src remote --platform linux/amd64`.
- De E2E startte om 00:09 CET. Daardoor viel de test `test_boten_zonder_plaats` over de datumgrens (zie hieronder). Ik had de starttijd moeten bewaken.

## Wat deed je zelf goed

- Na de mislukte test niets herhaald en direct gemeld.
- Het bewijs voor de dev-integratie als twee losse metingen vastgelegd: de leesquery en de logtelling met `--since <StartedAt>`.
- Gemeld dat er één `mislukt`-regel in het integratielog staat (503 van 17:08Z, vóór de run), en niet gezegd dat het er nul zijn.

## Wat heb je onderweg zelf verbeterd

- De vangnet-pull herkend als arm64 (de `Architecture` van het lokale image) en de scan voor amd64 opnieuw gedaan.
- Op de uitvoer van `draai.sh` een telscript gezet (per bestand geslaagd, mislukt, overgeslagen) in plaats van de regels te tellen.

## Wat kan structureel beter

- Zet in de opdracht: start de release-E2E niet tussen 23:00 en 01:00 Nederlandse tijd. De e2e-container draait op UTC en de app op Europe/Amsterdam, dus een test met `date.today()` verwacht dan een andere dag dan de app toont (gezien in `test_boten_zonder_plaats.py:35`, verwacht 25-11-2026, app toonde 26-11-2026). Open een issue om de test of de container op dezelfde tijdzone te zetten.
- Zet in de opdracht: haal het vangnetimage op met `docker pull` zonder `--platform` en scan het amd64-manifest met `trivy image --image-src remote --platform linux/amd64 <image>@<digest>`; een lokale pull geeft op deze Mac arm64.
- Zet in de opdracht: de unitsuite (circa 18 minuten) start als eerste in de achtergrond; trivy-builds mogen ernaast, de E2E pas daarna.
