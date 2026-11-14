# Retrospective milestone 5 "Features na v1.0.2"

Datum: 2026-11-14. Gesloten: #154, #159, #206, #262, #226, #255, #251, #258, #272 en #271 (release v1.1.0). Open binnen de milestone: geen. Input: de terugblikken van 2026-11-12 tot en met 2026-11-14 in `werk/terugblik/`.

## Wat werkte

- De E2E-suite draaide twee keer na elkaar groen op d86f0f3, met 50 geslaagd, 0 mislukt en 0 overgeslagen per run. De aantallen staan in #271, zoals de les uit milestone 4 vroeg.
- De lokale trivyscan vóór de tag vond 34 meldingen high in libpq5 die de release anders na het taggen hadden gestopt. Na #272 ging de release-workflow in één keer goed. Beide images hebben 1.1.0, 1.1 en latest op hetzelfde digest, en het app-image heeft libpq5 17.12.
- Reviewers draaiden mutanten tegen elke nieuwe controle, ook op sjablonen en sorteervolgorde (#154, #206).

## Wat beter kan

- De release-workflow gebruikte een buildcache, waardoor `apt-get` geen beveiligingsupdates meer ophaalde. Dat bleef onzichtbaar tot de lokale scan het met dezelfde cache naliet. Opgelost in #272; de lokale scan bouwt voortaan met `--no-cache` (overlay v0.5.81).
- E2E-mutanten op sjablonen liepen niet omdat `DRAAI_OVERRIDE` `web` niet opnieuw aanmaakt (#206). De regel is aangepast (overlay v0.5.79).
- Een sorteermutant overleefde omdat de planner een index koos, niet omdat de test sterk genoeg was (#154). Les in de overlay (v0.5.80): `ANALYZE` en een controlerun.
- Een lange E2E-run in slaapstand duurde uren en liep over de inloggrens (#262). Les in de overlay (v0.5.78).

## Waar de lessen landen

Alle lessen staan in `docs/PROJECT-OVERLAY.md` v0.5.74 tot en met v0.5.81. Er staat geen open werk in deze milestone. De volgende milestone vraagt eerst een voorstel aan de stakeholder.
