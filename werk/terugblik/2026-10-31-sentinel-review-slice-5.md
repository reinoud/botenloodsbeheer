# Terugblik sentinel, review slice 5

Datum: 2026-10-31. Taak: review van de gestagede wijziging van slice 5 (issue #19). Oordeel: niet akkoord, één punt.

## Wat ging goed

De opdracht gaf de norm, de verwachte waarden en de afwijkingen van de bouwer. Daardoor kon ik per criterium een test zoeken in plaats van te raden wat goed is. De stack draaide al en `nieuwe_database` stond in de conftest. De unitsuite draaide in één keer: 263 geslaagd, 0 mislukt, 0 errors, 0 overgeslagen. `alembic heads` geeft één head (0005). Los gedraaid met `tests/e2e/draai.sh test_api.py -k ik`: 1 geslaagd, 3 niet geselecteerd.

Per criterium uit de definition of done:

| Criterium | Test |
|---|---|
| BLB-029 crit. 1, API standaard aan | `test_ik_geeft_naam_rechten_en_vervaldatum_en_logt_zonder_waarde`; E2E `test_ik_via_de_interne_server` |
| BLB-029 crit. 2, uit via de omgeving | `test_api_uit_weigert_elke_aanroep` zet de config direct; de omgeving zelf is niet getest (mutant overleeft) |
| BLB-029 crit. 3, geen scherm | geen test; er is geen route, dus niets om te muteren |
| BLB-029 crit. 4, publieke server | `test_web_kent_de_api_niet`; E2E `test_publieke_server_kent_de_api_niet` |
| BLB-031 crit. 1, één keer tonen en logregel `cli` | `test_cli_maakt_en_trekt_in`, `test_robot_zonder_whitelist_en_dagen_krijgt_koppelnet_en_365_dagen` |
| BLB-031 crit. 2, `KOPPELNET` en 365 dagen | `test_robot_zonder_whitelist_en_dagen_krijgt_koppelnet_en_365_dagen`, `test_ik_geeft_...` |
| BLB-031 crit. 3, boven 3 jaar | `test_geldigheid_hooguit_3_jaar` (1095 mag, 1096 niet), `test_cli_weigert` |
| Intrekken met logregel | `test_intrekken_met_logregel`, `test_cli_maakt_en_trekt_in`, geval `ingetrokken` in `test_weigeringen_geven_hetzelfde_antwoord_en_een_logregel`; E2E `test_weigeringen` |
| BLB-032 crit. 1, zonder recht | `test_zonder_of_met_onbekend_recht_geweigerd`, `test_cli_weigert` |
| BLB-033 crit. 1 en 2, IPv4 en IPv6, buiten de lijst gelogd | `test_whitelist_ipv6`, geval `buiten_whitelist`, `test_whitelist_met_ipv4_en_ipv6`; E2E `test_weigeringen` |
| BLB-033 crit. 3, ongeldige whitelist | `test_ongeldige_whitelist_geweigerd`, `test_cli_weigert` |
| BLB-034 crit. 1, zonder of ongeldig token | gevallen `zonder`, `ander_schema`, `onzin`, `prefix_klopt_geheim_niet`, `verlopen` |
| BLB-034 crit. 4, 429 met `Retry-After` | E2E `test_boven_60_per_minuut_429_met_retry_after` |
| BLB-034 crit. 5, log zonder waarde | `test_ik_geeft_...`, `test_robot_zonder_whitelist_...` |
| BLB-034 crit. 6, `openapi.yaml` | `test_openapi_is_geldig_en_beschrijft_elke_route` |
| Migratie | `test_migratie_omkeerbaar_en_gelijk_aan_modellen` (eigen database), `test_api_rol_mag_tokens_niet_wijzigen`, `test_api_rol_mag_laatst_gebruikt_bijwerken`; `alembic heads`: 0005 |

De afwijkingen van de bouwer zijn gedekt of raken geen test: de prefix als sleutel (E2E 429), 1095 dagen (grens getest), 401 en 403 (statussen getest).

## Wat kon beter

Eén mutant overleeft. In `app/config.py` (`_schakelaar`) mag `return waarde == "true"` worden `return True`, en de hele suite blijft groen (263 geslaagd). De enige test op "uit" zet `config["API_INGESCHAKELD"]` direct. `API_INGESCHAKELD=false` in de omgeving is dus niet getest, terwijl het criterium juist "via de omgeving" zegt. Hetzelfde geldt voor een eigen `KOPPELNET` en de foutmelding bij een ongeldige waarde.

De E2E-test op 429 bewijst dat er een grens is, niet dat die op 60 per minuut staat. Een mutant met `rate=600r/m` of `burst=50` laat hem waarschijnlijk slagen. Dat is een vaste waarde in config; een minuut lang testen past niet bij het risico. Ik meld het, het blokkeert niet.

## Wat deed ik zelf goed

Ik heb de mutant echt gedraaid, met een gemuteerde `config.py` uit de scratchpad als volume over de testcontainer. Zo staat er geen vermoeden in het oordeel. De gedeelde database en de E2E-suite heb ik niet aangeraakt, op die ene `-k`-test na.

## Wat heb ik onderweg verbeterd

Eerst wilde ik de 404 op de publieke server als zwak markeren. Zonder het blok `location /api/` in `app.inc` slaagt de E2E-test nog, omdat `web` de route ook niet kent. Bij nalezen is dat juist de bedoeling: twee lagen, en de unittest dekt de tweede. Ik heb het niet als bevinding opgenomen.

## Wat kan structureel beter

Een instelling uit de omgeving wordt nu getest door de config in de test te overschrijven. Dat slaat het inlezen over.

Zet in de opdracht: "Elke nieuwe omgevingsvariabele krijgt een test die de variabele zet en `create_app` aanroept (geldige waarde en ongeldige waarde); een test die alleen `app.config` overschrijft, telt niet."
