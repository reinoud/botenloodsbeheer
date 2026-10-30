# Terugblik Sentinel: review slice 1a

Datum: 2026-10-30
Taak: review van de gestagede diff voor slice 1a (issue #1, BLB-022, BLB-024, BLB-025), met unit- en E2E-tests.

## Wat ging goed

De opdracht noemde de bronnen, de testcommando's en wie tests mocht draaien. Daardoor kon ik direct lezen en draaien zonder met Aegis te botsen. De stack draaide al; unit (42) en E2E (4) slaagden bij mij ook, zonder overgeslagen tests.

## Wat kon beter

Bij "log zonder persoonsgegevens" was niet vastgelegd of een gebruikersnaam van een beheerder daaronder valt. BLB-024 en ADR-006 noemen alleen adres, telefoon, e-mail en geheimen. Ik heb de gebruikersnaam toegestaan, maar dat is mijn lezing.

## Wat deed ik zelf goed

Ik heb de twee gaten die Forge meldde niet op zijn woord aangenomen. E2E-test 4 los gedraaid (`-k bezoeker`) faalt aantoonbaar. Bij het lezen van `totp_stap` vond ik dat `hmac.compare_digest` een TypeError geeft bij een code met niet-ASCII-tekens; dat heb ik met Python bevestigd.

## Wat heb ik onderweg verbeterd

Ik heb de rechten op het log in de migratie nagelopen tegen de tabellijst, omdat een brede GRANT op alle tabellen de beperking op `logregel` stil kon opheffen. `logregel` staat er terecht niet in.

## Wat kan structureel beter

Zet in de opdracht: "Noem bij een log-eis welke velden als persoonsgegeven gelden, ook gebruikersnamen van beheerders." En: "Een E2E-test hoort los te draaien; laat de reviewer één test met `-k` draaien als controle op volgorde."
