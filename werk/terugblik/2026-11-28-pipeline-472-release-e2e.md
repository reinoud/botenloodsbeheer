# Terugblik pipeline, 2026-11-28, trivy en release-E2E v2.7.2 (#472), project pl472, commit ab645b9

## Wat ging goed
- Er liep geen Time Machine-backup, dus de builds konden direct starten. Native arm64 en amd64 liepen naast elkaar; samen duurden ze circa 5 minuten.
- Trivy (0.76.2, `--ignore-unfixed`, CRITICAL en HIGH) vond niets in app, integratie en vangnet. De app had 35 doelen en de integratie 14, telkens met 0 bevindingen.
- De E2E draaide één keer in 31 minuten (16:58:33Z tot 17:29:49Z): 65 geslaagd, 0 mislukt, 0 overgeslagen, verdeeld over 32 pytest-runs. Er zijn 62 testfuncties; `vangnet/test_fase.py` heeft er één en draait vier keer (fasen gewoon, web_uit, api_uit, hersteld).
- `down -v` eindigde om 17:30:17Z. De dev-integratie gebruikte token 8390 om 17:32:28Z. Het aantal tokens bleef 21 en het log bevat sinds de start om 11:24:33Z geen regel `mislukt` of `401`.

## Wat kon beter
- De Mac liep bij de start op de accu (81%, nog 2:51 uur). Halverwege hing hij weer aan het net. De opdracht zegt niet wat er moet gebeuren bij accustroom.
- De eerste trivy-aanroep zonder `-q` gaf een voortgangsbalk van honderden regels in de uitvoer.

## Wat deed je zelf goed
- Vóór het bouwen gecontroleerd dat `tests/e2e/Dockerfile` en `requirements.txt` sinds v2.7.1 niet zijn gewijzigd. Daarom is `botenloods-e2e` niet opnieuw gebouwd.
- In de buildlog nagekeken wat `CACHED` was: alleen de basisimages met een vaste digest en één `WORKDIR`. Alle `RUN`-lagen zijn opnieuw gebouwd.
- De integratie gebouwd met dezelfde build-arg als de matrix in `images.yml`, en het vangnet op het amd64-manifest gescand met `--image-src remote`.

## Wat heb je onderweg verbeterd
- Trivy voor de images met `-q` gedraaid. De bevindingen geteld met een script op de rijen van de samenvatting, in plaats van de tabel met het oog te lezen.

## Wat kan structureel beter in de opdracht
- Zeg of de builds en de E2E mogen starten als de Mac op de accu loopt, en vanaf welk percentage niet.

## Als regel die de regie letterlijk kan overnemen
- Zet in de opdracht voor een release-E2E: "Leg met `pmset -g batt` de stroombron vast. Loopt de Mac op de accu onder 50%, wacht dan op netstroom voordat je bouwt. Draai trivy met `-q`."
