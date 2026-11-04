# Terugblik sentinel: review issue #45 (draai.sh in het nachtvenster)

**Datum:** 2026-11-04
**Taak:** review van de gestagede diff op `tests/e2e/draai.sh` tegen issue #45

## Wat ging goed

De opdracht noemde het criterium, de stand van de stack, het terugzetten naar `SYNC_TIJDSTIP=03:00` en het geval met een open verzoek. Daardoor kon ik zonder vragen beginnen. De code van de integratiecontainer is kort en maakte snel duidelijk dat de eerste ronde na de start een open verzoek oppakt.

## Wat kon beter

De eerste mislukte run van het open-verzoekscenario had ik niet vastgelegd; ik filterde de uitvoer te strak en moest het scenario herhalen om de oorzaak te zien. Die oorzaak (een 502 van Traefik bij de 413-test) staat los van de diff, maar kostte twee extra runs.

## Wat deed ik zelf goed

Ik heb de nachtproef niet alleen herhaald, maar eerst gecontroleerd dat er geen open verzoek stond en dat de container na het opnieuw maken niet uit zichzelf importeerde. Zo bewijst de geslaagde run echt het nachtpad. Het foutpad van de nieuwe regels heb ik met een stub in de scratchpad nagelopen (overlay §4).

## Wat heb ik onderweg verbeterd

Na de eerste onverklaarde fout heb ik elke volgende run volledig naar de scratchpad geschreven en pas daarna gefilterd. Zo vond ik de 502 in `test_vorm_en_grootte_via_traefik` op regel 56.

## Wat kan structureel beter

Zet in de opdracht: "Schrijf de volledige uitvoer van elke E2E-run naar je scratchpad en filter daarna; een mislukte run zonder uitvoer telt als niet onderzocht."

Zet in de opdracht: "Draai een E2E-scenario dat een criterium bewijst minstens twee keer; meld een fout die los staat van de diff apart, met test en regel."
