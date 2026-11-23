# Terugblik sentinel, derde review #372

**Datum:** 2026-11-23
**Taak:** derde review vóór de commit van issue #372 (404 van Traefik), na de afkeuring door aegis

## Wat ging goed

De brief noemde het herstel, de mutant die de regie al draaide en de databases die opgeruimd moesten worden. Daardoor kon ik direct naar de logica van `ronde` en `_fout`. De volledige unitsuite met een eigen `TEST_DB` liep in 7 minuten: 1795 geslaagd, 0 gefaald, 0 overgeslagen.

## Wat kon beter

De nieuwe test bewijst één patroon: strikte afwisseling van 200 en 404. Een ronde zonder import tijdens de wachttijd na een bronfout zet de telling ook terug, en dat patroon zat niet in de test. Een proef met het patroon 200, 200, 404 haalde de bron 40 keer op in 120 minuten. De brief vroeg niet naar andere volgordes dan die van aegis.

## Wat deed ik zelf goed

Ik heb de bevinding met een proef in de scratchpad aangetoond en een herstel van één regel (`if not wachten:`) met dezelfde proef en het hele testbestand gecontroleerd: 6 keer in 120 minuten, 66 van 66 tests geslaagd.

## Wat heb ik onderweg zelf verbeterd

De proef importeert de fixtures uit `tests/unit/test_integratie.py`, zodat er geen kopie van de nep-API nodig was. De rol voor `psql` is `botenloods`, niet `postgres`; dat stond in `conftest.py`.

## Wat kan structureel beter

Zet in de opdracht: "Bij een teller of wachttijd die een ronde terugzet, noem elke toestand waarin een ronde slaagt zonder het eigenlijke werk te doen (zoals een GET zonder import tijdens een wachttijd), en laat de test die toestand afwisselen met de fout, niet alleen het patroon uit de vorige review."

De database `botenloods_test_s372` van een eerdere reviewer bestaat nog. Die viel buiten deze opdracht en is niet verwijderd.
