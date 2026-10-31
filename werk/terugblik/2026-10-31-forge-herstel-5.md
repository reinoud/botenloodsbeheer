# Terugblik forge, herstel slice 5

Datum: 2026-10-31. Taak: de vier herstelpunten van slice 5 afmaken (issue #19): logbesluit, `API_INGESCHAKELD` uit de omgeving, AEG-01 en AEG-03.

## Wat ging goed

Het halve werk van de vorige forge was bruikbaar. Alle vier de punten stonden er al in, en `http.inc` bevatte geen achtergebleven mutant. Het werk bestond vooral uit nginx herstarten (die draaide al tien uur op de oude configuratie), de tests draaien en de mutanten bewijzen.

## Wat kon beter

De opdracht noemt de hele header als sleutel, ADR-005 regel 26 zegt een hash van de header. Nginx bewaart de sleutel van `limit_req_zone` in het gedeelde geheugen, dus de tokenwaarde staat daar nu wel. Dat had vóór de bouw bij foundation gemoeten. Ik heb het als afwijking gemeld.

Een mutant in `http.inc` is met `git diff` niet te zien: de gestagede versie heeft juist de prefix als sleutel. Ik heb het goede bestand met `cmp` tegen een kopie in de scratchpad vergeleken.

## Wat deed ik zelf goed

Mutanten op Python-code heb ik als volume over de testcontainer gezet, niet in de werkmap. Alleen de nginx-mutanten stonden kort in de werkmap, omdat nginx die bestanden leest. Ik heb ook een extra mutant gedraaid voor AEG-03 (zonder `limit_req_log_level`), zodat de controle op de foutlog iets bewijst.

## Wat heb ik onderweg verbeterd

Ik heb een mutant toegevoegd die weer een logregel schrijft bij een geslaagde aanroep. Die faalt op `test_ik_geeft_naam_rechten_en_vervaldatum_zonder_logregel`, dus het logbesluit is echt getest.

## Wat kan structureel beter

Zet in de opdracht: "Controleer een mutant in een bestand dat al gestaged is met `cmp` tegen een kopie, niet met `git diff`; een mutant die de gestagede versie terugzet, is in `git diff` onzichtbaar."
