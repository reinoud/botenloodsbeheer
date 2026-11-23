# Terugblik Sentinel, review #381

Datum: 2026-11-23. Taak: review vóór commit van issue #381 (lidnummers van ongeldige records op de statuspagina). Oordeel: niet akkoord, op één punt.

## Wat ging goed

De opdracht noemde precies wat al gedaan was (17 mutanten, unitsuite, E2E-run). Daardoor kon ik gericht zoeken naar wat ontbrak. De mutanten via een bind mount uit de scratchpad werkten in één poging; de werkmap bleef ongewijzigd (`git diff --stat` leeg).

## Wat kon beter

Een extra testbestand kan niet als los bestand in `/app/tests/unit` worden gemount, want die map is alleen-lezen en Docker kan er geen mountpunt maken. Ik moest een kopie van een bestaand testbestand met de extra test eroverheen mounten. Dat kostte één mislukte run.

## Wat deed je zelf goed

Ik las besluit 4 terug in de open vraag van het issue ("hoe lang hij bewaard blijft"). Daardoor zag ik dat het besluit over de bewaarduur gaat en niet alleen over de weergave. Een kleine test in de scratchpad toonde aan dat het lidnummer na een schone import in de vorige run in `taakrun` blijft staan, terwijl ADR-004 stap 2 zegt dat de lijst tot de volgende import blijft.

## Wat heb je onderweg zelf verbeterd

Eerst zag ik de bewaarduur als een vraag voor Aegis. Na het nalezen van de grants (`UPDATE` op `taakrun` voor `botenloods_api`, migratie 0006) en de opschoning (ruimt `taakrun` nooit op) kon ik een herstel van een paar regels zonder migratie voorstellen.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Bewaart de wijziging een persoonsgegeven, noem dan in de opdracht de afgesproken bewaarduur en laat de bouwer een test schrijven die na afloop van die duur de rij in de database controleert, niet alleen het scherm."

Zet in de opdracht: "Mutanten op tests leveren de tester als overlay van een bestaand bestand aan (`-v <scratch>/x.py:/app/tests/unit/<bestaand>.py:ro`); een nieuw bestand in de alleen-lezen testmap mounten lukt niet."
