# Retrospective milestone 3 "Onderhoud na v1.0.0"

Datum: 2026-11-11. Gesloten: #235, #232, #233, #234, #231, #236, #172, #217, #213, #237 en #247 (release v1.0.1). Open: #230, alleen nog criterium 2 (Dependabot ziet de voorbeeldmap). Input: de achttien terugblikken van 2026-11-11 in `werk/terugblik/`.

## Wat werkte

- Elke wisselvallige test kreeg eerst een proef die zonder herstel faalt: `stijl.css` blokkeren voor #172 en #217, ruisregels in het log voor #213. Daarna was de E2E-suite zes keer groen zonder herhaling.
- Aegis vond in #232 dat `unaccent` een breed `％` omzet in een wildcard (AEG-01). Dat kwam vóór de merge boven en werd met een nareview gesloten.
- De Trivy-scan vóór het taggen maakte de release van v1.0.1 in één keer goed.

## Wat beter kan

- #230 sloot via `Closes` terwijl criterium 2 pas na de merge te toetsen is, en zonder slotcommentaar. Les in de overlay (v0.5.68): `Refs` bij zo'n criterium.
- Een eerste volgordeproef voor #213 bewees niets, omdat de ruis dezelfde actie was als de gezochte regel. Les in de overlay (v0.5.70).
- De proef van de bouwer liet ongeveer 110 beheerders `e2e-ruis-*` achter in de lokale database. Les in de overlay (v0.5.70): ruis via `log.schrijf`, niet via de interface.
- Docs op `main` terwijl een agent de werkmap op een branch had, vroeg een aparte worktree. Dat werkte, maar kost een extra stap.

## Waar de lessen landen

Alle lessen staan in `docs/PROJECT-OVERLAY.md` v0.5.61 tot en met v0.5.70. Voor de volgende afstemming: #240 (tekst bij eigenaar onbekend), #243 (whitelist `0.0.0.0/0` bij een robottoken, vraagt een besluit), de nieuwe index-digest van Traefik v3.7.17 (Dependabot stelt die voor) en de achtergebleven beheerders `e2e-ruis-*` in de lokale database.
