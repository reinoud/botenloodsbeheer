# Terugblik Aegis, security-herreview issue #381

Datum: 2026-11-23. Taak: herreview vóór commit van het herstel van AEG-381-01 (lidnummers bleven in eerdere `ledenimport`-runs staan). Oordeel: akkoord.

## Wat ging goed

De opdracht noemde het punt uit de eerste review, de drie toetsvragen en wat de regie al had gedraaid (unittests, mutant, E2E). Daardoor hoefde ik niets te herhalen en kon ik direct de paden in `importeer` en `import_mislukt` nalopen. De vraag naar de databaserol was terecht: de test draait via `als_api` met `botenloods_api`, dezelfde rol als de dienst api in `docker-compose.yml`, zodat de unittest de rechten (GRANT in 0006, rijbeleid in 0014) echt raakt.

## Wat kon beter

De opdracht zei niet dat er naast `botenloods` nog ruim twintig testdatabases in dezelfde container staan. Ik heb ze alle alleen-lezen geteld (overal 0 rijen met de sleutel), maar dat kostte een extra stap.

## Wat deed ik zelf goed

Ik heb het herstel bevestigd op de echte stack: run 1686, die in de eerste review de lijst nog vasthield, heeft de sleutel niet meer, en de imports van 20:16 tot 20:18 liepen via de dienst api. Ik heb alleen id, status, tijdstip en een ja/nee op de sleutel opgevraagd, geen lidnummers. Ik heb geen test gedraaid, omdat Sentinel tegelijk de gedeelde database gebruikte.

## Wat heb ik onderweg zelf verbeterd

Eerst wilde ik het pad met de Veiligheidsgrens met een eigen test in de scratchpad bevestigen. Dat zou de tabellen leegmaken die Sentinel op dat moment gebruikte. Ik heb het pad daarom in de code nagelopen: de `UPDATE` staat in `_run_afsluiten` en draait na de rollback in de nieuwe transactie, vóór de commit.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Draait er tegelijk een andere reviewer op de gedeelde testdatabase, noem dan welke databases in de container van de reviewer zijn en welke de reviewer alleen-lezen mag bevragen."
