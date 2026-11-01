# Terugblik Bedrock: wachtlijst vervolg (slice 7, issue #43)

Datum: 2026-11-02. Taak: vier punten na de review (andere eigenaar, racetest `eraf_halen`, clubplaats, lege datum).

## Wat ging goed

De vier punten waren klein en goed afgebakend. De bestaande helper `_eraf` droeg de nieuwe reden zonder aanpassing. Elke mutant faalde op de bedoelde test.

## Wat kon beter

Mijn eerste invoeging van de lege-datumtest was een no-op in het script (een `if False`-restant), en mijn eigen test miste de import van `acties`. Beide zag ik pas in de mutantrun.

## Wat deed ik zelf goed

Ik draaide de mutanten tegen het hele testbestand en controleerde dat de mutant `is None` echt overleefde totdat de test er stond. Zo viel de ontbrekende test op.

## Wat heb ik onderweg verbeterd

De test voor de logverwijzing las `b.lid_id` na de wijziging en toetste daardoor het nieuwe lid. Nu gebruikt hij het oude lid.

## Wat kan structureel beter

- Zet in de opdracht: "Draai na het toevoegen van een test eerst de mutant die hij moet vangen; een mutant die overleeft, betekent dat de test niet is toegevoegd of niets toetst."
- Zet in de opdracht: "Een unittest die tijdzonegevoelig is (`date.today()` naast `vandaag()`) faalt tussen 00:00 en 02:00 Amsterdamse tijd; noem welke bekende testfouten daardoor verwacht zijn."
