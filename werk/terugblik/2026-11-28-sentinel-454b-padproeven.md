Datum: 2026-11-28. Taak: tweede review vóór commit van issue #454, herstel van `WACHT=1` bij `klant.py pad` (sentinel).

## Wat ging goed

- De brief noemde het ene blokkerende punt, de drie wijzigingen en twee patchbestanden om te vergelijken. Met `diff` tussen `diff-454.patch` en `diff-454b.patch` zag ik binnen een minuut wat nieuw was.
- De run van de regie (134 OK, 0 FOUT) lag klaar. Ik hoefde `padproeven.sh` en `draai.sh` niet opnieuw te draaien.

## Wat kon beter

- `diff-454b.patch` bevat alleen de code; de ADR en de terugblikken staan er niet in. Dat bleek pas toen `cmp` met de huidige staging afweek. De brief kan zeggen welke paden in een patchbestand zitten.
- De geslaagde live run bewijst niet dat het wachten werkt: Traefik kan de router al kennen na `up --wait`. Dat moest ik zelf aantonen.

## Wat deed je zelf goed

- Het herstel getoetst met een nep-Traefik in de scratchpad (eerst drie keer 404, dan 200): `pad` met `WACHT=1` slaagt en zonder faalt; `status` gedraagt zich gelijk aan de versie op `main`; `rem` wacht niet. Zonder docker, in een paar seconden, op de versie uit de index.
- In bash nagegaan dat `WACHT=1 controle ...` via twee functies bij `klant` aankomt en niet doorlekt naar de volgende controle.

## Wat heb je onderweg zelf verbeterd

- Eerst wilde ik `draai.sh` draaien voor het gedrag van `status`. De vergelijking met `klant.py` van `main` tegen dezelfde nep-Traefik gaf hetzelfde bewijs in seconden in plaats van twee minuten.

## Wat kan structureel beter in de opdracht of de afspraken

- Zet in de opdracht: "Een herstel van een wacht- of herhaallus in `tests/proxy/klant.py` toets je eerst met een lokale nep-upstream in de scratchpad (eerst 404, dan 200) op de versie uit de index, met en zonder de variabele; een live run telt alleen als aanvulling."
