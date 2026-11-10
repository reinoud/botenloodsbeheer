# Retrospective milestone v1.0.0 release

Datum: 2026-11-11. Issues: #221, #223 en #196, alle drie gesloten (PR #228, #227 en #229). Daarnaast de securityronde (`werk/security/2026-11-10-aegis-statisch.md` en `2026-11-10-probe-dast.md`) en release v1.0.0. Input: de terugblikken van sentinel, aegis en probe van 2026-11-10 in `werk/terugblik/`.

## Wat werkte

- De drie issues liepen naast elkaar in eigen worktrees. Daardoor wachtte geen enkele review op een andere.
- De securityronde vond niets met ernst hoog of middel. De vier bevindingen van probe uit de vorige ronde zijn alle opgelost.
- Een Dependabot-PR binnen de cooldown kreeg de nieuwste versie die wel oud genoeg was (uv 0.13.5). Zo hoefde de release niet te wachten.

## Wat beter kan

- Een mutant met het filter alleen in `haal_leden` overleefde de eerste test van #221. Een filter in een gedeelde functie heeft per aanroeper een test nodig. Die les staat in de overlay (Algemeen).
- De eerste oordelen van de reviewers kwamen niet aan, omdat ze naar `team-lead` waren gestuurd. Les in de overlay: stuur ze naar `main`.
- Bij het draaien van de unitsuite vanuit een worktree startte een tweede database. De bestaande overlayregel over `-p botenloods` was over het hoofd gezien. Die regel is aangevuld met het env-bestand en `secrets/`.
- `Closes #<nr>` sloot het issue bij de merge zonder slotcommentaar. Les in de overlay (§4): het slotcommentaar komt vóór de merge.

## Waar de lessen landen

Alle lessen staan in `docs/PROJECT-OVERLAY.md` v0.5.57 tot en met v0.5.60. Voor de volgende afstemming staan open: #226, #230, #231, de adviespunten AEG-09 (inloggegevens van e-boekhouden als secret) en AEG-10 (`exclude-newer` ophogen), en de melding van probe dat de seed 11 rekken en 229 plaatsen maakt in plaats van 10 en 160.
