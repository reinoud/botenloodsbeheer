# Terugblik Sentinel, review herstel issue #28

**Datum:** 2026-10-31
**Taak:** review van de gestagede diff voor issue #28 (verzoek van een beheerder na een fout)

## Wat ging goed
De brief gaf de norm per uitkomst (bron, 409, andere HTTP-fout, netwerk, onverwacht) en het mutantcommando. Daardoor kon ik zeven gerichte mutanten maken die elk een tak raken. Alle zeven faalden.

## Wat kon beter
`ruff check` geeft één fout in `tests/unit/test_beheerders_beheren.py:214` (ISC004), buiten deze diff. De brief zei niet of een bestaande lintfout blokkeert.

## Wat deed je zelf goed
De mutanten gegenereerd met een script dat controleert dat elke vervanging precies één keer voorkomt, zodat geen mutant ongemerkt gelijk bleef aan het origineel.

## Wat heb je onderweg zelf verbeterd
Vóór de E2E-run `draai.sh` gelezen: het script zet zelf een nieuw token en herstart de integratiecontainer, dus `draai.sh test_import.py` was de juiste losse aanroep.

## Wat kan structureel beter
Zet in de opdracht: "Een lintfout buiten de diff blokkeert de review niet; meld bestand:regel en of er al een issue voor is."
