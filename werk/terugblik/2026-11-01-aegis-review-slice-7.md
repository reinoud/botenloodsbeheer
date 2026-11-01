# Terugblik aegis: securityreview slice 7 (wachtlijst)

Datum: 2026-11-01. Taak: securityreview van de gestagede diff van slice 7 (#43, #27).

## Wat ging goed

De brief noemde de toetspunten en de normen per punt (ADR-001, ADR-005, ADR-006 v1.2.0, ADR-012). Daardoor kon ik elk punt direct tegen een ADR-zin leggen. De rechten in de migratie waren in de draaiende database na te lopen met `\dp`, zonder iets te wijzigen.

## Wat kon beter

De brief noemde niet welke test als de rol `botenloods_api` draait. Ik moest zelf in `tests/unit/conftest.py` en `tests/unit/test_leden.py` zoeken of de import met de echte rechten van api getest wordt (positieve controle). Dat bleek zo te zijn.

## Wat deed je zelf goed

Ik heb de rechten in de database gecontroleerd en niet alleen in de migratie gelezen. Ik heb gecontroleerd dat de test op #27 de actor, de verwijzingen en de gegevens van de logregel volledig vergelijkt, zodat er geen persoonsgegeven bij kan komen zonder dat de test faalt.

## Wat heb je onderweg verbeterd

Ik toetste eerst of de wachtlijstroutes `recent_ingelogd` nodig hebben. De overlay beperkt ADR-001 tot een link, een nieuw account of een nieuwe inlogmethode; toewijzen gebruikt het ook niet. Ik heb dat punt daarom laten vallen in plaats van het als bevinding te melden.

## Wat kan structureel beter

Zet in de opdracht: "Noem bij een domeinfunctie die een nieuwe databaserol raakt de test die als die rol draait (marker of fixture), zodat de reviewer de positieve controle niet zelf hoeft te zoeken."
