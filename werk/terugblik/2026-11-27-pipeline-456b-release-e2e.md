# Terugblik pipeline, 2026-11-27, release-E2E v2.7.1 (#456), project pl456b, commit 75f0790

## Wat ging goed
- Native arm64-images met `--no-cache` onder `pl456b` gebouwd; `docker image inspect` bevestigde arm64. Netstroom gecontroleerd (`pmset`).
- Eén run, niets herhaald: 64 geslaagd, 1 mislukt, 0 overgeslagen (32 pytest-runs, geteld met een script). `test_status.py` (5 tests, incl. de ongeldige-records-test) en de vier vangnetruns slaagden.
- Logs van traefik, api, web, integratie, worker en `docker inspect` van api bewaard vóór `down -v`.
- De dev-integratie bleef werken: token laatst gebruikt 16:53Z (voor de run) en 18:00:18Z (na `down -v` 17:24:50Z), geen nieuw token.

## Wat kon beter
- De hook Blast Radius hield `rm secrets/api_token.pl456b` twee keer tegen (10 minuten wachten per keer, ook gebundeld met `down -v`). Het bestand (0 bytes) staat er nog: de regie ruimt het op.
- De mislukte test (`test_lid_koppeling.py::test_koppelen_oud_lid_status_en_loskoppelen`, `Page.goto` naar `/uitnodiging/...` na 30 s time-out, 140 s) is niet onderzocht: herhalen mocht niet en de stack is weg.
- Eén regel `Import mislukt (HTTP 404)` in het dev-integratielog om 16:54:14Z (tijdens de run), dev-Traefik gaf 404 op `/api/v1/leden/importverzoek`; geen 401, daarna weer 200. Oorzaak onbekend.

## Wat deed je zelf goed
- Verwarring tussen logtijd (CET) en UTC opgelost vóór de vergelijking met `--since`.
- Wachten in lussen van hooguit 480 s.

## Wat heb je onderweg verbeterd
- `rm` en `down -v` niet in één commando; `down -v` eerst, tijdstip vastgelegd.
- Env-variabelen in een `env.sh` in de scratchpad, zodat elke compose-aanroep (logs, down) dezelfde project- en tagwaarden had.

## Wat kan structureel beter in de opdracht
- Zeg dat het tokenbestand van het project door de regie wordt verwijderd (de hook houdt `rm` tegen), of geef een goedgekeurd pad.
- Noem dat het dev-integratielog tijdens de run een eigen 404 kan tonen, en of dat telt.

## Als regel die de regie letterlijk kan overnemen
- Zet in de opdracht voor een release-E2E: "Het agent laat `secrets/api_token.<project>` staan en meldt het pad; de regie verwijdert het. Een enkele `Import mislukt (HTTP 404)` van de dev-integratie tijdens de run wordt gemeld met het tijdstip, niet opgelost."
