# Terugblik sentinel, review herstel slice 5

Datum: 2026-10-31. Taak: review van het gestagede herstel van slice 5 (issue #19). Oordeel: akkoord, met één open punt dat buiten de code valt.

## Wat ging goed

De opdracht noemde per punt de toets en de norm. Daardoor was elke toets een mutant of een telling. Uitkomsten:

| Toets | Bewijs | Uitkomst |
|---|---|---|
| 1. Geslaagd geen logregel, weigering wel en zonder waarde | `test_ik_geeft_naam_rechten_en_vervaldatum_zonder_logregel`; `test_weigeringen_geven_hetzelfde_antwoord_en_een_logregel`. Mutant: logregel in `tokens.gebruikt` | mutant faalt (1 mislukt) |
| 2. Omgeving via `create_app` | `test_api_aan_of_uit_via_de_omgeving`, `test_eigen_koppelnet_...`, `test_ongeldige_instelling_stopt_het_starten`. Mutant: `return True` in `_schakelaar` | mutant faalt op `[false-403]` |
| 3. AEG-01 | Mutant in `http.inc`: prefix als sleutel; `-k nep_geheim` | mutant faalt (`assert 429 == 200`); teruggezet, `cmp` gelijk, nginx herladen en `cmp` in de container gelijk |
| 4. Suites | unit: 270 geslaagd, 0 mislukt, 0 errors, 0 overgeslagen. E2E (5 bestanden): 18 geslaagd, 0 mislukt, 0 overgeslagen. `-k nep_geheim` los: 1 geslaagd. `test_api.py` na het terugzetten: 5 geslaagd | groen |

Na de 429's gaf nginx één toegangslogregel per verzoek in het formaat `zonder_code` en geen regel in de foutlog.

## Wat kon beter

ADR-005 regel 26 zegt dat de sleutel van de rate limit een hash van de header is. Gebouwd is de hele header, dus de tokenwaarde staat in het gedeelde geheugen van nginx. Stock-nginx kan geen hash in een `map` maken. De bouwer meldde het, maar er is geen issue of ADR-wijziging. Dat moet er zijn voordat #19 dichtgaat; het oordeel over het risico is aan foundation en aegis.

De grens per IP (300 per minuut) en de exacte waarde 60 per minuut zijn alleen in config te zien, niet getest. Past bij het risico; ik meld het.

## Wat deed ik zelf goed

Ik controleerde eerst of de draaiende nginx dezelfde `http.inc` las als de gestagede versie. Anders had een groene E2E-run niets over de diff gezegd. De Python-mutanten stonden als volume uit de scratchpad, de werkmap bleef ongewijzigd op de korte nginx-mutant na.

## Wat heb ik onderweg verbeterd

Ik wilde de nginx-mutant eerst overslaan, omdat de redenering sluitend leek. Toets 3 vraagt een bewijs, dus ik heb hem gedraaid met `nginx -s reload` in plaats van een herstart. Dat was sneller en raakte de andere diensten niet.

## Wat kan structureel beter

Zet in de opdracht: "Een gemelde afwijking van een ADR krijgt vóór de review een issue of een ADR-wijziging; een melding alleen in een terugblik of issuecommentaar telt niet."
