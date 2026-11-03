# Terugblik sentinel

**Datum:** 2026-11-03
**Taak:** review van de gestagede securityrestpunten (#59, #61, #62, #64, #67, #68, #69, #72)

## Wat ging goed

De opdracht noemde de omgeving, het koppelnet, de verdeling met aegis en de afwijking van de issuetekst (`/p/%00` geeft 400). Daardoor kon ik direct toetsen en hoefde ik niets te raden. Alle zes mutanten vielen met een duidelijke assert.

## Wat kon beter

Mijn eerste mutantrun gebruikte `-k`, terwijl overlay §4 een run tegen het hele testbestand vraagt. De opdracht zei "draai één nieuwe test los met `-k`", en dat las ik eerst ook als regel voor de mutanten. Ik heb de mutanten daarna opnieuw tegen de hele bestanden gedraaid.

## Wat deed ik zelf goed

Ik bouwde de mutanten zelf uit de gestagede bronnen en controleerde ze met `cmp`, in plaats van die van de regie over te nemen. Ik controleerde de SHA's van de actions tegen de tags op GitHub en de digest van trivy. Ik probeerde ook padvarianten buiten de issuetekst (`//uitnodiging/`, `/./`, `/x/../`) via de proxy. Traefik schoont die op, dus de code bleef gemaskeerd.

## Wat heb ik onderweg verbeterd

De mutanten opnieuw gedraaid tegen het hele testbestand en de commando's in `commando.txt` naast de mutanten gezet. Ruff faalde in de container op de cache; met `--no-cache` werkte het.

## Wat kan structureel beter

Zet in de opdracht: "Mutanten draai je tegen het hele testbestand (overlay §4); `-k` geldt alleen voor de losse run van een nieuwe test."
Zet in de opdracht: "Ruff in de testcontainer draai je met `--no-cache`, want de map is alleen-lezen."
