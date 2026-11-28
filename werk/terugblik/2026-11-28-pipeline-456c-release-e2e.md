# Terugblik pipeline, 2026-11-28, release-E2E v2.7.1 (#456), project pl456c, commit 75f0790

## Wat ging goed
- Eén volledige run, niets herhaald: 65 geslaagd, 0 mislukt, 0 overgeslagen (32 pytest-runs, geteld met een script). De vier vangnetfasen staan als vier aparte runs van `vangnet/test_fase.py` in het log. `git diff --stat 490929b 75f0790` toonde alleen `tests/e2e/test_status.py`, de overlay en terugblikken.
- Native arm64-images met `--no-cache` gebouwd en gecontroleerd. Netstroom (AC, 100%) en hosttoestand vooraf vastgelegd. Logs en `docker inspect` van api bewaard vóór `down -v`.
- Geen time-out en geen `Import mislukt` tijdens de run.
- Dev-integratie na `down -v` (01:10:29Z): token 8390 gebruikt om 01:12:51Z, tokenaantal gelijk (21), 0 regels `mislukt` of `401` sinds het opruimen.

## Wat kon beter
- Er liep een Time Machine-backup (FindingChanges, daarna Copying). Wachten duurde van 00:46 tot 01:39 CET, circa 53 minuten, in lussen van 8 minuten.
- Het dev-integratielog eindigt nog met `Import mislukt (HTTP 404)` van 17:54:14Z (gisteren, de hapering uit #461). Sindsdien geen regel meer, dus de vooraf vastgelegde toestand is geen `Import geslaagd`.
- `docker stats` vooraf toonde de worker op 106% CPU; na de backup 0%. Toeval of oorzaak is niet bekend.

## Wat deed je zelf goed
- Logtijd (UTC) en hostklok (CET) uit elkaar gehouden; `down -v` met `date +%s` vastgelegd en 150 seconden gewacht.
- Tokenbestand niet verwijderd; `down -v` zonder `rm`, dus geen blokkade door de hook.

## Wat heb je onderweg verbeterd
- `docker logs --since 01:10:29` werkt niet (alleen duur of volledige datum); gecorrigeerd naar `2026-11-28T01:10:29Z`.
- Env in `env.sh` in de scratchpad, zodat elke compose-aanroep dezelfde waarden had.

## Wat kan structureel beter in de opdracht
- Zeg welke tijd de wachttijd voor een Time Machine-backup mag duren, of dat de run mag starten als de backup meer dan een uur duurt.
- Zeg of een oude `Import mislukt (HTTP 404)` als laatste regel van het dev-integratielog vooraf telt als 401-achtige uitgangstoestand.

## Als regel die de regie letterlijk kan overnemen
- Zet in de opdracht voor een release-E2E: "Loopt er een Time Machine-backup, plan dan ruim een uur extra; bouw de images pas na de backup. Gebruik voor `--since` een volledige UTC-datum (`2026-11-28T01:10:29Z`), niet alleen een kloktijd."
