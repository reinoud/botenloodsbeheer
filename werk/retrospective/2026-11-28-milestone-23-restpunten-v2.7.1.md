# Retrospective milestone 23

Datum: 2026-11-28. Milestone 23 "Restpunten vangnet, Dependabot en E2E-tijdzone, v2.7.1" is met v2.7.1 gesloten (#440, #447, #448, #449, #456, #458). Input: de terugblikken van 2026-11-27 en 2026-11-28 in `werk/terugblik/`.

## Wat werkte

- De oorzaak van #458 werd met het weblog bewezen (een verschil van 272 bytes tussen twee keer `GET /status`) voordat er een fix kwam. Er volgde één gerichte wijziging, die in twee volledige runs slaagde.
- Bij de update naar Traefik v3.7.18 zijn de proeven van ADR-013 herhaald. Aegis vond daarbij een extra hardening (`POST /;a/inloggen` valt nu ook onder de rate limit).
- Na een mislukte release-E2E werd niets herhaald zonder besluit van de stakeholder. Elke herhaling kreeg een eigen project (pl456b, pl456c).

## Wat beter kan

- Twee van de drie release-E2E's faalden, en geen van beide keren door de release: eerst een race in een test (#458), daarna een hapering van de Docker-host tijdens een Time Machine-backup (#461). Elke herhaling kost ongeveer 90 minuten.
- Sentinel gaf bij #440 geen akkoord op de documentatie: er stond een onjuiste zin over het beheerdersverzoek in en de 503 ontbrak in twee teksten. Bij een gedragswijziging nam de regie niet alle teksten mee.
- De regie zette een geschatte tijd in een bericht aan de stakeholder in plaats van die op te halen.
- `draai.sh` krijgt paden zonder `tests/e2e/`; met het voorvoegsel stopt pytest met exit 4.

## Waar de lessen landen

- Overlay v0.6.42 tot en met v0.6.45: TZ in de e2e-container, `expect` in plaats van `all_inner_texts()`, de hosttoestand vooraf vastleggen, een time-out door de host herkennen, `--since` met een UTC-datum, en het tokenbestand dat de stakeholder verwijdert.
- Issues: #459 (dezelfde race bij `count()`) en #461 (hapering van de host; dicht na drie runs zonder hapering).
- Geheugen: `tijd-in-antwoord` (elk antwoord begint met de tijd, opgehaald met `date`).
- Documentatie bij een gedragswijziging: valt onder de bestaande regel dat geraakte documenten in dezelfde ronde worden bijgewerkt. Er komt geen nieuwe afspraak.
