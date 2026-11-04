# Terugblik sentinel, issue #91

**Datum:** 2026-11-04
**Taak:** review van de gestagede diff voor #91 (413 via Traefik in plaats van 502)

## Wat ging goed

De brief noemde de oorzaak, de acceptatiecriteria, het testcommando en wie de suites draait. Daardoor kon ik direct beginnen en botste ik niet met aegis.

## Wat kon beter

De brief vroeg naar lege en chunked lichamen, maar niet naar paden buiten de views van de blueprint. Juist daar zat het gat: een te groot verzoek op een onbekend pad of met een verkeerde methode valt buiten `bp.errorhandler`, krijgt een HTML-413 zonder weglezen en geeft af en toe 502.

## Wat deed ik zelf goed

Ik heb de oorzaak bevestigd zonder de werkmap of de draaiende api te wijzigen: de route zonder weglezen (onbekend pad) dient als controlegroep en gaf 5 keer 502 op 40 verzoeken, de route met weglezen 0 op 40.

## Wat heb ik onderweg verbeterd

Mijn eerste proef liep op de rate limit per token (429). Daarna gaf ik elk verzoek een eigen Authorization-kop, zodat alleen de limiet per adres telde.

## Wat kan structureel beter

Zet in de opdracht: "Toets een foutafhandeling ook op een onbekend pad en een verkeerde methode onder hetzelfde prefix; een `bp.errorhandler` dekt die niet, een `bp.app_errorhandler` wel."

Zet in de opdracht: "Een proef met veel verzoeken via Traefik gebruikt per verzoek een eigen Authorization-kop en blijft onder 50 verzoeken per adres, anders meet je de rate limit."
