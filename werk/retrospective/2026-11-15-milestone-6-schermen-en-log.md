# Retrospective milestone 6 "Schermen en log na v1.1.0"

Datum: 2026-11-15. Gesloten: #270, #169, #192, #265, #267, #174, #216, #218, #167, #164, #153, #149, #161 en #209. Open binnen de milestone: #288 (release v1.2.0). Input: de twintig terugblikken van 2026-11-14 en 2026-11-15 in `werk/terugblik/`.

## Wat werkte

- Design System toetste elke schermwijziging vóór of naast de review, zonder de lokale stack. Bij #192 hield die toets een meldingswijziging tegen die tegen een later besluit van de stakeholder inging (BV-71 na BV-68).
- Sentinel vond in drie van de vijf bouwrondes een echt gat: een gelijkwaardig verklaarde mutant die dat niet was (#167, M6), een niet bewaakt criterium (#174, gegevens in het log) en documentatie die een niet bestaande handeling beloofde (#164). Elk herstel ging naar een verse reviewer.
- Kleine wijzigingen deed de regie zelf (#267, de herstelrondes van #218, #174 en #164). Dat scheelde een bouwagent per ronde.

## Wat beter kan

- Subagents wachtten drie keer op een melding van Monitor die niet aankwam en vielen stil. De regel staat nu letterlijk in elke opdracht: wachten met een until-lus in de voorgrond (overlay v0.5.84).
- De regie legde de stakeholder bij #164 een vraag voor die uitging van een functie die niet bestaat. Het besluit moest opnieuw. Voortaan gaat de regie vóór zo'n vraag in de code na dat de handeling bestaat (v0.5.87).
- Een bouwagent startte een tweede E2E-run bovenop de eerste en wijzigde `draai.sh` tijdens een run (#192, testfixes). Beide regels stonden al in de overlay en staan nu ook in de opdrachten.
- Alle reknaamletters voor E2E-tests zijn op (#218). Een nieuwe E2E-test breidt voorlopig een bestaande uit.

## Waar de lessen landen

De lessen staan in `docs/PROJECT-OVERLAY.md` v0.5.82 tot en met v0.5.87. Restpunten uit de reviews staan als issue voor de volgende afstemming: #268 en #275 (ontwerpbesluiten van Design System), #278 (ruisbeheerders in de E2E-database), #279 (meetpunt 1060 px), #283 (slottest op plaatsen) en #285 (commentaar en herstel in de uploadtest).
