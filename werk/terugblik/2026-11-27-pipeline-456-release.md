# Terugblik pipeline, 2026-11-27, controles vóór release v2.7.1 (#456), commit 490929b

## Wat ging goed
- De overlayregels waren volledig genoeg om de run zonder vragen uit te voeren: volgorde, tags, override en token per project klopten.
- Unit (1858 geslaagd) en trivy draaiden naast elkaar zonder conflict dankzij een eigen testdatabase.
- De dev-integratie bleef na `down -v` intact (token gebruikt 15:40:29Z, 0 regels `mislukt` of `401`).

## Wat kon beter
- De E2E-run duurt ruim 35 minuten; `until`-lussen van 590 seconden tellen als te lang en worden afgebroken (exit 144). Wacht in lussen van hooguit 500 seconden.
- De afgekapte `tail` op meerdere bestanden gaf een abort-melding door een niet-UTF8 tabelrand in het trivylog; ik heb daarna met `grep -c` geteld.
- Bij de mislukte test heb ik de oorzaak niet kunnen vaststellen: de stack moest voor `down -v` weg, en herhalen mocht niet.

## Wat deed je zelf goed
- Logs van traefik, api, integratie, web, worker en `docker inspect` van api bewaard vóór `down -v`.
- Eindtijd van `down -v` genoteerd en na twee minuten de leesquery gedraaid.
- `botenloods-app:latest` bleek ouder dan `app/`, dus ik bouwde native `pl456` met `--no-cache`.

## Wat heb je onderweg verbeterd
- Eigen `conftest.py` met `TEST_DB=bl_test_456a` gemaakt met python3 en na afloop de database met `DROP DATABASE ... WITH (FORCE)` verwijderd.

## Wat kan structureel beter in de opdracht
- Zeg welke E2E-uitkomst volstaat bij een testfout die niet door de release komt (zoals v2.7.0 met #449): melden en doorgeven, of de regie beslist.
- De opdracht noemt de vangnetfasen als "vier fasen van vangnet.sh"; zeg dat die als vier aparte pytest-runs (`vangnet/test_fase.py`) in het log staan.

## Als regel die de regie letterlijk kan overnemen
- Zet in de opdracht voor een release-E2E: wacht in lussen van hooguit 500 seconden, want de run duurt circa 37 minuten; en meld bij een mislukte test of het log van de statuspagina (`/status`) bewaard moet blijven voor de analyse.
