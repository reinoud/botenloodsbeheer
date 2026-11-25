# Terugblik Pipeline, 2026-11-25, release v2.6.2 (#437)

## Wat ging goed
Alles slaagde in één keer op 280b2fa: unitsuite 1855 geslaagd, trivy 0 CRITICAL en 0 HIGH voor app en integratie, E2E 61 geslaagd op 61 testfuncties, workflow Images groen, digests van 2.6.2, 2.6 en latest gelijk per image. Het dev-token werd na `down -v` gebruikt zonder 401.

## Wat kon beter
De eerste controle van het dev-token gaf een gebruik van vóór `down -v` (13:32:54 tegenover 13:33:01); ik moest een lus draaien tot een gebruik erna. De hostklok (CET) en de containerlogs (UTC) verschillen een uur, wat bij het lezen van de integratielogs verwarrend is.

## Wat deed je zelf goed
Ik heb het e2e-image gecontroleerd op alle pakketten uit `requirements.txt` en de native architectuur van de nieuwe images, vóór de run. Unitsuite en E2E draaiden niet tegelijk. Tellingen kwamen uit een script.

## Wat heb je onderweg verbeterd
De wachtlus voor het dev-token vergelijkt het tijdstip met het eindtijdstip van `down -v` in plaats van een vaste wachttijd.

## Wat kan structureel beter in de opdracht
Zet in de opdracht: "Noteer het eindtijdstip van `down -v` in UTC (`date -u`) en wacht in een lus tot `laatst_gebruikt_op` later is; het eerste gebruik kan nog van vóór `down -v` zijn."
