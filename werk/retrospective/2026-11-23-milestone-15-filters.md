# Retrospective milestone 15 "Filters en restpunten"

Datum: 2026-11-23. Gesloten: #380 (filters zonder knop), #379 (menuknop op een smal scherm op één lijn) en #378 (vaste override voor de release-E2E). Nieuw restrisico: #384. Input: de terugblikken van 2026-11-23 bij #378, #379 en #380 in `werk/terugblik/`.

## Wat werkte

- #379 en #378 haalden elk de review in één ronde. Meten vóór herstellen vond de echte oorzaak van #379 (een algemene `details`-marge), niet het vermoeden uit de opdracht.
- De toets van Design System kwam binnen tijdens de review en leverde een aandachtspunt in hun README op.
- De proefrun van #378 slaagde in één keer (59 van 59) naast de lokale stack, zonder die te raken.

## Wat beter kan

- Mijn opdracht voor #379 noemde een oorzaak en een rolaanname (kijker zonder zoekveld) uit het hoofd; beide klopten niet.
- De reviewbrief van #379 noemde de vaste werkwijze voor een CSS-mutant niet; de reviewer zette de mutant in de werkmap.
- Bij #378 hield de hook het verwijderen van het tokenbestand tegen; het bestand verdween pas met de worktree.

## Waar de lessen landen

- Overlay v0.6.23: bron voor zichtbaarheid per rol, oorzaak alleen als vermoeden, mutant via bind mount noemen in een reviewbrief.
- Overlay v0.6.24: `RELEASE_TAG` bij elke compose-aanroep, e2e-image opnieuw bouwen bij een gewijzigde runner, tokenbestand als de hook de `rm` tegenhoudt, scripts in een worktree.
- Menuknop in oudere browsers: #384.
