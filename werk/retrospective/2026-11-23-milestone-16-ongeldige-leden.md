# Retrospective milestone 16 "Ongeldige leden zichtbaar en v2.3.0"

Datum: 2026-11-23. Gesloten: #381 (lidnummers van ongeldige records op de statuspagina) en #387 (release v2.3.0). Input: de terugblikken van 2026-11-23 bij #381 en #387 in `werk/terugblik/`.

## Wat werkte

- Sentinel en Aegis vonden onafhankelijk dezelfde fout in de bewaartermijn, elk met een proef; het herstel haalde de herreview in één ronde.
- De release-E2E slaagde in één run (60 van 60) met de vaste override uit #378, zonder aanpassing. Het dev-token bleef gelijk.
- De regie draaide de E2E van een worktree zelf na overname van de diff in de hoofdwerkmap; zo had de review een geslaagde run.

## Wat beter kan

- Mijn opdracht voor #381 zei dat een kijker de statuspagina kon openen; de stakeholder corrigeerde dat. Tweede rolaanname uit het hoofd in één dag (ook #379).
- De bouwopdracht noemde de bewaartermijn alleen voor het scherm, niet voor de database; daardoor bleven lidnummers in oude runs staan tot de review.
- Milestone 15 ging dicht zonder release; de stakeholder moest ernaar vragen.

## Waar de lessen landen

- Overlay v0.6.25: kijkerrechten in `KIJKER_TOEGESTAAN`, bewaarduur getoetst in de database, E2E bij een worktree, unittests bij twee reviewers.
- Overlay v0.6.26: tijdstip in UTC bij het bewijs na het opruimen.
- Release: een milestonevoorstel zegt voortaan of de milestone met een release eindigt (geheugen, `milestones-afstemmen`).
