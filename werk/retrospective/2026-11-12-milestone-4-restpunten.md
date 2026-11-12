# Retrospective milestone 4 "Restpunten na v1.0.1"

Datum: 2026-11-12. Gesloten: #214, #230, #240, #176, #208, #243 en #257 (release v1.0.2). Open binnen de milestone: geen. Input: de terugblikken van 2026-11-12 in `werk/terugblik/`.

## Wat werkte

- De lokale Trivy-scan op `git archive 2befbfb` was schoon, en de release-workflow ging in één keer goed. Beide images hebben 1.0.2, 1.0 en latest op hetzelfde digest.
- Reviewers draaiden mutanten tegen elke nieuwe controle. Bij #243 viel de mutant `<` naar `<=` ook in een schermtest die de brief niet noemde.
- Besluiten van de stakeholder (#243, #214) kwamen vóór de bouw in de brief.

## Wat beter kan

- De brief bij #214 noemde niet welke gevallen van fout naar geaccepteerd gaan als een weigering smaller wordt. `clubboot;1001` bij een lid met een andere naam is nu een ledenboot, zonder test en zonder zin in de handleiding. Les in de overlay (v0.5.71, versmalde weigering).
- Briefs noemden regelnummers en bestaande controles op de verkeerde plek (#214) en mutanten zonder verwachte falende assert (#240, #176). Lessen in de overlay (v0.5.71 en v0.5.72).
- De oorzaak van de Dependabot-fout bij #230 is niet lokaal na te spelen; het herstel is een hypothese. Controle na de merge staat in de overlay (v0.5.71).
- Bij de release van v1.0.2 stonden de aantallen van de twee E2E-runs nergens vast. Les in de overlay (v0.5.73).

## Waar de lessen landen

Alle lessen staan in `docs/PROJECT-OVERLAY.md` v0.5.71 tot en met v0.5.73. Voor de volgende afstemming: milestone 5 "Features na v1.0.2" (#206, #159, #154), restpunt #255 (test op een persoonlijk token met een brede whitelist) en #226 (Def2 met een hoofdletter, ernst laag).
