# Retrospective milestone 8 "Oud-leden als eigenaar en SBOM"

Datum: 2026-11-18. Gesloten: #300, #297, #295, #298, #307 en #303 (release v1.3.0, getagd op 2026-11-17). Input: de 25 terugblikken van 2026-11-17 in `werk/terugblik/`.

## Wat werkte

- Opdrachten met de bronnen in volgorde van gezag en de besluiten per vraag gaven bouw zonder eigen ontwerpkeuzes (#298 bij bedrock, apex en foundation; #295 met BV-85 boven de issuetekst).
- Een besluit dat het formaat vastlegde, hield #297 klein: één andere vlag van Trivy maakte de SBOM, zonder nieuw image of nieuwe tool.
- Een klaargezette mutant met diff en uitvoer liet de reviewer zonder eigen run zien dat precies de nieuwe test faalt (#295, derde review).

## Wat beter kan

- Een besluit uit een ander issue botste met oudere criteria (BV-72 uit #295 tegen BLB-046 en BLB-013 bij #298). De opdracht noemde #295 alleen voor de keuzelijst.
- Regelnummers zonder bestand en lijsten met regelnummers misten plekken; zoeken op de inhoud vond ze wel (#298, sentinel en foundation).
- De opdracht van #295 zei niet wat een ongewijzigd, gevuld veld Eigenaar betekent. Dat gat kwam pas na de bouw terug als #316.
- Een bouwer wijzigde sjablonen terwijl zijn basissuite liep; dat gaf drie valse falers (#298).
- De isolatie van een worktree weigerde Bash-regels met het pad van de scratchpad in een subshell; een script in de scratchpad werkte wel (#297).

## Waar de lessen landen

De lessen staan in `docs/PROJECT-OVERLAY.md` v0.5.93 tot en met v0.5.96 (19 regels over bouw, review, E2E en security). Restpunten werden issues in milestone 9: #316 (lange lidnaam), #321 (Boten zonder eigenaar als lijst), #323 (restpunten review #298) en #327 (eerste import na #298). De eerste ledenimport na de uitrol nakijken staat in #328, bij de stakeholder.
