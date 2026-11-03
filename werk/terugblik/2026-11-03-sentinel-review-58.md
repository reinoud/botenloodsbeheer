# Terugblik

**Datum:** 2026-11-03
**Taak:** review van de gestagede diff voor issue #58 (Pillow 13.0.0, `formats`, pytest 9.0.3)

## Wat ging goed
De opdracht noemde de omgeving, de bekende failure (#64), de afsplitsing naar #63 en de besloten melding. Daardoor kon ik zonder zoeken toetsen. Diff klein, mutant en e2e in een paar minuten gedraaid.

## Wat kon beter
De opdracht zei niet of ik het e2e-image zelf mocht herbouwen. `draai.sh` bouwt het niet, dus zonder `build e2e` had de e2e-run de oude pytest getest. Ik heb het herbouwd, omdat de vraag anders niet te beantwoorden was.

## Wat deed ik zelf goed
De versies in het image (`pip list`) en in `web` gecontroleerd vóór de e2e-run, zodat de groene test echt pytest 9.0.3 en Pillow 13.0.0 bewijst. Mutant met `python3` gemaakt, de diff tegen het origineel getoond en als bind mount gedraaid.

## Wat heb ik onderweg zelf verbeterd
Ik heb eerst gezocht naar uploadtests in `test_loods.py` in plaats van te raden: er is er één, met PNG (`test_indeling_boot_toewijzen_log_en_openbare_pagina`).

## Wat kan structureel beter
Zet in de opdracht: "Wijzigt `tests/e2e/requirements.txt`, herbouw dan eerst het e2e-image met `docker compose -f docker-compose.yml -f compose.dev.yml --profile e2e build e2e` en controleer de versies met `pip list` vóór `draai.sh`; `draai.sh` bouwt niet."
