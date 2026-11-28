# Retrospective milestone 24

Datum: 2026-11-28. Milestone 24 "Restpunten tijd, E2E en proxyproeven, v2.7.2" is met v2.7.2 gesloten (#452, #454, #459, #472). Input: de terugblikken van 2026-11-28 bij deze issues in `werk/terugblik/`.

## Wat werkte

- De release-E2E slaagde in één run: 65 geslaagd, 0 mislukt, 0 overgeslagen, met de vier vangnetfasen als aparte runs. Er was geen herhaling nodig, anders dan bij milestone 23.
- Trivy vond niets in app, integratie en vangnet. De tags 2.7.2, 2.7 en latest hebben per image dezelfde digest.
- Aegis rekende bij #452 de wintertijd na volgens PEP 495 en vond de vergelijkingen in de unittests die het dubbele uur raken.

## Wat beter kan

- Drie van de vier issues hadden een tweede review nodig (#452, #454, #459). Bij #454 telden de bouwer en de regie groene runs als bewijs voor de wachtlogica; een snelle run bewijst niet dat er gewacht wordt.
- Een commentaarregel van 104 tekens kwam door de bouw, want ruff controleert E501 niet in dit project (#452). Er staan er meer in de integratie (#466).
- De oordelen bij #459 gingen uit van de pagina vóór de klik, terwijl een helper eerst `page.goto` doet.
- De release-E2E startte terwijl de Mac op de accu liep (81%). Dat ging goed, maar de opdracht zei er niets over.

## Waar de lessen landen

- Overlay v0.6.46 tot en met v0.6.49: regellengte tellen met python3, tijd- en datumcode in de review, tellingen in helpers en lussen na een klik, `expect_navigation()`, lange proefscripts in de achtergrond, de functie die een variabele van `klant.py` leest, rate limit met gedeelde teller, `--help` uit een lokaal image, en de stroombron vastleggen vóór een release-E2E.
- Issues: #466 (te lange commentaarregels in de integratie), #469 (padproef `/api/v1/%2Fik` ook op websecure), #461 (stand: twee van de drie release-E2E's zonder hapering).
- De Python-versie in een reviewbrief valt onder de bestaande afspraak in `~/.claude/CLAUDE.md` (Agentopdrachten). Er komt geen nieuwe afspraak.
