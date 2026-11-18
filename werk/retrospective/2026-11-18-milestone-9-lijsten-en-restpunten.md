# Retrospective milestone 9 "Lijsten, restpunten en afhankelijkheden na v1.3.0"

Datum: 2026-11-18. Gesloten: #315, #316, #319, #320, #321, #323, #327 en #337 (release v1.4.0). Input: de terugblikken van bouwers en reviewers in `werk/terugblik/` en de scratchpad van de regie.

## Wat werkte

- Ontwerp eerst bij Design System (#315, #321) en twee besluiten vooraf aan de stakeholder (bootsoort tonen, uitklapblok dicht): de bouw had geen open keuzes.
- Reviewers die zelf een mutant maakten, vonden wat de tests misten: de sorteersleutel `Boot.id` (#315) en de grens van 123 tekens (#316, als #333 vastgelegd).
- #327 haalde een omweg weg in plaats van hem te documenteren; de E2E-suite is weer groen op een verse stack, ook bij de release (twee keer 54 geslaagd).

## Wat beter kan

- Oordelen van reviewers kwamen twee keer uren niet aan, terwijl de suites klaar waren (#315, #316, #321 's nachts; de herreview van #315 overdag). De regie wachtte op een melding en keek niet zelf in de scratchpad. Dat kostte bij elkaar ongeveer negen uur.
- De cooldown van 14 dagen voor Dependabot stond niet in de eerste opdrachten voor #319 en #320; een bouw moest over.
- Een reviewer bouwde het gedeelde image opnieuw vanuit een worktree (#321). Het bleef zonder gevolg, omdat de bestanden gelijk waren.
- De regie startte de E2E-runs voor de release zonder stack; `draai.sh` start die niet zelf.

## Waar de lessen landen

Elf regels in `docs/PROJECT-OVERLAY.md` v0.5.97, onder meer: een oordeel gaat met SendMessage én in het eindantwoord, en de regie kijkt zelf in de scratchpad. Restpunten als issue: #333 (grenstest lange lidnaam) en #331 (handleiding Uitloggen). Een webinterface met Swagger voor de API ligt als vraag bij de stakeholder.
