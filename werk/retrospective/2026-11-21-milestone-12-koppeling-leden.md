# Retrospective milestone 12 "Koppeling met leden en v2.2.0"

Datum: 2026-11-21. Gesloten: #348 (jezelf geen kijker maken zonder andere beheerder met inlogmethode), #354 (na het inloggen terug naar de opgevraagde pagina), #353 (gebruiker koppelen aan een lid, in twee delen), #345 (`ds-radio`) en #356 (release v2.2.0). Tussendoor: #360 (communityprofiel) en #362 (tag oud-lid op /leden). Input: de terugblikken van 2026-11-20 en 2026-11-21 in `werk/terugblik/`.

## Wat werkte

- Bij #353 lagen het schermontwerp (BV-96) en ADR-015 v1.3.1 vast vóór de bouw van deel 2. De toets van Design System gaf daarna akkoord zonder herstelpunten, en Sentinel en Aegis keurden in één ronde goed.
- De mutantdiscipline hield stand: elke nieuwe test kreeg een mutant met de falende assert als bestand:regel, en reviewers konden ze opnieuw draaien.
- De release v2.2.0 had alle criteria op de eerste dag, met een eigen project voor de E2E zoals de les uit milestone 11 vroeg.

## Wat beter kan

- Agents rapporteerden twee keer iets onjuist over hun eigen werk: prism noemde een uitvoerbestand dat niet bestond, en Sentinel vermoedde ten onrechte dat de E2E-mutanten van prism niet hadden gedraaid. De regie vond het pas door de uitvoer zelf te lezen.
- De hook Blast Radius hield de release-E2E tegen, omdat het akkoord van de stakeholder niet in de opdracht stond.
- Run 1 van de release-E2E faalde op één 404 van Traefik. Dat had de regel van één run (besluit van vandaag) direct geraakt; het onderzoek staat in #368.
- `draai.sh` maakte het token van de dev-stack ongeldig, net als bij #347. De les van milestone 11 (herstart) was niet genoeg.
- Een les uit de terugblik van Sentinel (#345) stond al in de overlay (#206) en kwam er dubbel in.

## Waar de lessen landen

- Overlay v0.6.5 tot en met v0.6.11: de lessen per oplevering (Bouw, Review, E2E).
- Overlay v0.6.13: één E2E-run voor een release (besluit van de stakeholder).
- Overlay v0.6.14: akkoord voor de release-E2E vooraf vragen en een nieuw robottoken voor de dev-stack daarna.
- Overlay v0.6.15: dubbele regel over `DRAAI_OVERRIDE` weg. Voortaan zoekt de regie vóór een nieuwe regel in de overlay op een kernwoord (zoals `DRAAI_OVERRIDE`).
- De regie leest de uitvoerbestanden zelf voordat een telling naar de stakeholder gaat; dat staat al in de algemene afspraken en bleek hier nodig.
- Issues: #364 (melding bij loskoppelen, 400-pagina), #366 (`bl-radio`), #368 (404 van Traefik en het token van de dev-stack).
