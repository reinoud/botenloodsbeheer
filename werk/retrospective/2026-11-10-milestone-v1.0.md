# Retrospective milestone v1.0 eerste testversie

Datum: 2026-11-10. Issues: #203, #205 en #220, alle drie gesloten (PR #222, #225 en #224). Input: de terugblikken van bedrock, sentinel en aegis bij deze issues in `werk/terugblik/`.

## Wat werkte

- Een ontwerpvraag aan Design System vóór de bouw (BV-74) gaf de bouwer een vast schermontwerp. De toets achteraf vond geen afwijking.
- #220 in een eigen worktree met een eigen wegwerpstack kon naast de bouw van #205 lopen, zonder dat de gedeelde stack werd geraakt.
- Mutanten per kant en per pad lieten zien dat elk pad van de vervallen regel een eigen test heeft.

## Wat beter kan

- De twee branches gaven `architectuur.md` hetzelfde versienummer. De regie loste dat op bij de rebase. Les in de overlay (Bouw).
- De review van #205 viel op één zin in de handleiding, die de oude regel als voorbeeld van een weigering noemde. Gezocht was op de tekst van de oude melding, niet op de omschrijving van het geval. Les in de overlay (Bouw).
- Bij #220 bleek het gebrek uit het issue (lege afbeelding) niet te bestaan; de afbeelding was alleen te kort afgesneden. Les in de overlay (Bouw).

## Waar de lessen landen

Alle lessen staan in `docs/PROJECT-OVERLAY.md` v0.5.55 (bij #203) en v0.5.56 (bij #205 en #220). Restpunt: #223 (foutroutes in `draai.sh`).
