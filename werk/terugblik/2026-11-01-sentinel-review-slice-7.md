# Terugblik sentinel: review slice 7 (wachtlijst)

**Datum:** 2026-11-01 (run liep door tot 2026-11-02 00:20)
**Taak:** review van de gestagede diff van slice 7, issue #43 en #27

## Wat ging goed

- De brief gaf verwachte waarden, bronnen en de grenzen van de review. Daardoor kon ik elke regel in `app/domein/wachtlijst.py` direct tegen een criterium leggen.
- De mutanten liepen als bind mount in één lus over vijf testbestanden: 19 mutanten in ongeveer zes minuten, zonder de werkmap te raken.
- De unitsuite (410 geslaagd) en de E2E-suite (28 geslaagd) slaagden zonder overgeslagen tests.

## Wat kon beter

- `tests/e2e/draai.sh` faalde na middernacht: de integratiecontainer importeert pas na `SYNC_TIJDSTIP` (03:00) of op een verzoek. Ik verloor tijd voordat ik dat zag, en mijn eerste wachtlus las nog het oude uitvoerbestand.

## Wat deed ik zelf goed

- Voor de mutant die overleefde (geen slot in `eraf_halen`) schreef ik meteen een racetest in de scratchpad die hem doodt. De bouwer kan die overnemen.
- Ik heb aegis vooraf en achteraf gemeld dat `draai.sh` het token vervangt.

## Wat heb ik onderweg verbeterd

- Ik omzeilde de nachtgrens zonder de werkmap te wijzigen: eerst een importverzoek via `leden.import_aanvragen`, getimed tussen twee rondes van de draaiende container, en daarna `draai.sh`.
- Voor de wachtlus gebruik ik nu een vast tijdstip, niet de inhoud van een bestand dat een vorige run al vulde.

## Wat kan structureel beter

- Zet in de opdracht: "Draai `tests/e2e/draai.sh` niet tussen 00:00 en `SYNC_TIJDSTIP`; of laat `draai.sh` eerst een importverzoek doen in plaats van op de geplande import te wachten."
- Zet in de opdracht: "Schrijf de uitvoer van elke run naar een nieuw bestand met een tijdstempel in de naam, niet naar hetzelfde bestand."
