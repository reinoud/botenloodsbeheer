# Retrospective milestone 13 "Restpunten en v2.2.1"

Datum: 2026-11-21. Gesloten: #358 (basis 1.0.x, was al gedaan), #366 (`ds-radio` op Token maken), #364 (Lid koppelen, foutpagina voor 400), #368 (E2E: wachten op de router, tokenbestand per project) en #369 (release v2.2.1). Nieuw: #372 (404 van Traefik in de integratiecontainer) en #374 (ingetrokken token na `draai.sh` op de dev-stack). Input: de terugblikken van 2026-11-21 bij #364, #366, #368 en #369 in `werk/terugblik/`.

## Wat werkte

- Elke diff met een gedeelde foutafhandeling of een tokenbestand kreeg Sentinel en Aegis naast elkaar. Hun adviespunten (een CSRF-test, een tokenbestand alleen onder `secrets/`) kwamen klein en gericht, en een verse reviewer toetste alleen het herstel.
- De release-E2E in pl369 slaagde in één run (58 van 58). De logs van vóór `down -v` waren er dit keer wel.
- Pipeline vond de echte oorzaak van de 401 op de dev-stack door tijdstempels en tokenmetadata naast elkaar te leggen, in plaats van het token stil te vervangen.

## Wat beter kan

- Pipeline meldde bij #368 dat de dev-integratie na zijn run zonder 401 importeerde. Het log liep tot kort vóór het opruimen; de 401 kwam erna. Een controle direct na het einde van de run had dat getoond.
- Een eerste review van #364 viel uit door een netwerkfout. De regie moest de review opnieuw starten.
- Het verwijderen van een bestand werd twee keer door de hook tegengehouden, ook na akkoord van de stakeholder.
- De oorzaak van de 404 uit #356 is niet bewezen; criterium 1 van #368 is daarom aangepast.

## Waar de lessen landen

- Overlay v0.6.16: bij alleen sjablonen en CSS draait de reviewer de geraakte testbestanden, de regie de volledige suite.
- Overlay v0.6.17: bij een nieuwe statuscode in een gedeelde foutafhandeling elke bron noemen.
- Overlay v0.6.18: tokenbestand per project, werkmap op de releasecommit tijdens de release-E2E, logs bewaren vóór `down -v`.
- Overlay v0.6.19: toestand van de dev-integratie vooraf vastleggen, nieuw token na `draai.sh` op de dev-stack tot #374, tokenbestand als losse stap verwijderen.
- Nieuw in deze retrospective: een controle op de dev-integratie gebeurt ná het opruimen van `draai.sh`, niet tijdens de run. Dat valt samen met #374 en landt daar als acceptatiecriterium ("ook na het opruimen").
- Issues: #372 en #374.
