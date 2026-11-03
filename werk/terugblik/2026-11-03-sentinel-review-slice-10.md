# Terugblik sentinel, review slice 10

**Datum:** 2026-11-03
**Taak:** review vóór de commit van slice 10 (#51): dekking van de criteria, mutanten, unit- en E2E-suite, documentatie met schermafbeeldingen en migratie 0009.

## Oordeel

Akkoord. Geen bevinding blokkeert. Vier punten met ernst laag staan hieronder.

| # | Bestand:regel | Ernst | Punt |
|---|---|---|---|
| 1 | `app/domein/tokens.py:125-145` | laag | `rechten_wijzigen` neemt een `FOR UPDATE`-slot, maar er is geen racetest met twee sessies en het issue noemt niet waarom die ontbreekt (overlay §4). Zonder slot kan `oud` in de logregel verouderd zijn; de rechten zelf blijven juist. |
| 2 | `app/domein/tokens.py:145` | laag | `nieuw != oud` vergelijkt lijsten met volgorde. Een CLI-token met rechten in een andere volgorde dan `RECHTEN` geeft bij ongewijzigd opslaan in het scherm een logregel `token.rechten_gewijzigd` met dezelfde rechten in `oud` en `nieuw`. |
| 3 | `tests/unit/test_integratie.py:345` | laag | BLB-042 criterium 7 is getoetst op de tekst van het label (`${API_EXTERN_BRONNEN:?`), niet met `docker compose config` met en zonder waarde. Die regel kwam in overlay v0.3.17, na de bouw. Ik heb het met de hand nagelopen: zonder waarde stopt compose met exit 1 en de melding uit het label; met waarde staan de allowlist en de router op `websecure` in de config; zonder het bestand is er geen router `api-extern`. |
| 4 | `tests/unit/test_persoonlijke_tokens.py:126` | laag | BLB-030 criterium 5 en BLB-042 criteria 2 tot en met 6 (proxy, vervalste kop, 429, 403 van Traefik) hebben geen herhaalbare test in de suite; alleen de proef van forge met een losse Traefik. Ik heb die proef niet herhaald; aegis toetst dit deel. |

Buiten de diff: ruff geeft ISC004 in `tests/unit/test_beheerders_beheren.py:214`, al bekend in #32.

## Testruns

- Unitsuite: 517 geslaagd, 0 mislukt, 0 overgeslagen, 0 errors (`scratchpad/sentinel-slice10/unit-101554.txt`).
- E2E, volledige run met `tests/e2e/draai.sh`: 35 geslaagd over 10 bestanden, 0 mislukt, 0 overgeslagen, 0 errors (`e2e-102240.txt`). Los: `-k test_token_van_een_collega_intrekken` 1 geslaagd, 34 niet geselecteerd.
- Vóór de runs: alleen `docs/PROJECT-OVERLAY.md` had niet-gestagede wijzigingen; dat pad wordt niet gemount. De code in `web` en `api` is gelijk aan de gestagede versie (`cmp` op vijf bestanden).

De scratchpadpaden staan onder `/private/tmp/claude-502/-Users-reinoud-git-botenloods/eb8ddbe2-0198-41c2-a9b5-a21ddd9c6096/scratchpad/sentinel-slice10/`.

## Criteria en tests

| Criterium | Test |
|---|---|
| BLB-030.1 waarde één keer | `test_nieuw_token_toont_de_waarde_eenmalig_zonder_sessie`, `test_persoonlijk_token_hoort_bij_de_maker_met_logregel_zonder_waarde`, E2E `test_persoonlijk_token_maken_wijzigen_en_intrekken` |
| BLB-030.2 hooguit 3 jaar | `test_persoonlijk_token_hooguit_3_jaar` (1095 mag, 1096 niet), scherm in `test_nieuw_token_geweigerd_houdt_de_invoer` |
| BLB-030.3 geblokkeerd of verwijderd | `test_geblokkeerde_eigenaar_weigert_tot_deblokkeren` (ook deblokkeren), `test_verwijderen_neemt_persoonlijke_tokens_mee_als_web` |
| BLB-030.4 geen `leden:importeren` | `test_persoonlijk_token_zonder_leden_importeren`, scherm en rechten wijzigen geparametriseerd |
| BLB-030.5 lege whitelist | `test_persoonlijk_token_met_lege_whitelist_werkt_vanaf_elk_adres`; proxydeel zie punt 4 |
| BLB-030.6 herstellen | `test_herstellen_laat_het_persoonlijke_token_werken` |
| BLB-031.4 robot in het web | `test_nieuw_token_toont_de_waarde_eenmalig_zonder_sessie`, `test_robot_uit_de_webinterface_heeft_een_whitelist_en_onthoudt_de_maker` |
| BLB-031.5 en .6 maker vertrekt | `test_robot_blijft_werken_na_vertrek_van_de_maker` |
| BLB-032.3 boot zonder persoonsgegevens | `test_boten_zonder_persoonsgegevens_alleen_naam_en_lidnummer`, `test_geen_persoonsgegeven_zonder_het_recht` |
| BLB-032.4 rechten wijzigen | `test_rechten_gelden_vanaf_de_volgende_aanroep_met_logregel`, `test_ongeldige_rechten_wijzigen_niets`, E2E |
| BLB-034.2 en .3 leesaanroepen | `test_elke_leesroute_vraagt_haar_recht` (403 en schema), `test_leden_op_lidnummer_zonder_en_met_persoonsgegevens`, `test_plaatsen_in_de_volgorde_van_het_overzicht`, `test_wachtlijst_per_bootsoort_langst_wachtend_eerst_zonder_oud_leden` |
| BLB-035.1 overzicht | `test_overzicht_toont_alles_behalve_waarde_en_hash` |
| BLB-035.2 token van een ander | `test_token_van_een_ander_intrekken`, E2E `test_token_van_een_collega_intrekken` |
| BLB-035.3 recente inlog | `test_recente_inlog_vereist_voor_maken_wijzigen_en_intrekken` (601 seconden, vier routes), `test_overzicht_kan_zonder_recente_inlog` |
| BLB-042.1, .7 | `test_api_van_buiten_alleen_met_compose_api_extern` en de handcontrole uit punt 3 |

## Mutanten

Elke mutant draaide als bind mount over het bestand in de testcontainer, tegen de volledige bestanden `test_persoonlijke_tokens.py`, `test_leesaanroepen.py`, `test_tokens.py` en `test_beheerders_beheren.py`. Alle twaalf zijn gevangen. Commando's in `mutanten/commando.txt` en `mutanten/draai.sh`, uitvoer in `mutanten/uit-102101.txt`.

| Mutant | Falende assert |
|---|---|
| m1 eigenaar inactief weg (forge) | `test_persoonlijke_tokens.py:149` `(200, []) == (401, ...)` |
| m2 lege whitelist weigert (forge) | `:131` `401 == 200` en drie andere |
| m3 altijd persoonsgegevens in domein (forge) | `test_leesaanroepen.py:89`, `:107`, `:123`, `:134` |
| m4 `leden:importeren` toegestaan (forge) | `DID NOT RAISE Regelfout` (twee tests), `:286` |
| m5 intrekken zonder recente inlog (forge) | `:306` `302 == 302 and False` |
| s6 geen logregel bij rechten wijzigen | `:202` `not enough values to unpack` |
| s7 aantal tokens weg uit log | `:168` en `test_beheerders_beheren.py:88` |
| s8 overzicht zonder maker | `:189` `'<td ...>bert</td>' in ...` |
| s9 rechten wijzigen zonder recente inlog | `:306` |
| s10 API geeft altijd persoonsgegevens | `test_leesaanroepen.py:89`, `:107`, `:123`, `:134` |
| s11 rechten wijzigen zonder soort | `DID NOT RAISE Regelfout` in `test_ongeldige_rechten_wijzigen_niets` |
| s12 robot zonder whitelist toegestaan | `IntegrityError robot_met_whitelist` in plaats van `Regelfout`; de check in de database vangt hem als tweede laag |

## Migratie 0009

Op een eigen database (`sentinel_mig_slice10`, na afloop verwijderd): één head (`0009`). Na upgrade heeft `botenloods_api` `SELECT` op `beheerder.id` en `beheerder.actief`, niet op `gebruikersnaam`, en `SELECT` op `rek` en `plaats_bootsoort`; `botenloods_web` heeft geen `DELETE` op `token`. Downgrade naar 0008 haalt die rechten en de twee kolommen weg en verwijdert een persoonlijk token; een robottoken blijft staan. Een robottoken van vóór 0009 krijgt `gemaakt_door = 'cli'`, zonder blijvende standaardwaarde. Opnieuw upgraden geeft dezelfde rechten. Eerdere migraties gaven `api` geen rechten op `rek`, `plaats_bootsoort` of `beheerder`, dus de `REVOKE` in de downgrade neemt niets weg wat er al was.

## Documentatie

`documentatie/gebruikers/handleiding.md` heeft een hoofdstuk Tokens met de soorten, rechten, blokkeren, deblokkeren en herstellen, en vier nieuwe schermafbeeldingen. `token-waarde.png` toont `blb_<waarde>` en geen echte waarde. `tokens.png` op 1100 pixels toont acht kolommen zonder afkappen. De beheerdocumentatie heeft `api-van-buiten.md` en de aanpassingen in installatie, bijwerken en integratiecontainer (409 tijdens de opschoning, uit #49). De andere schermafbeeldingen veranderen door het nieuwe menu-item; ik heb er twee steekproefsgewijs bekeken.

## Wat ging goed

De brief noemde de criteria, de besluiten van 2026-11-03 en de plek van de mutanten van forge. Daardoor kon ik per criterium een test zoeken en de mutanten van forge direct naast die van mij draaien. De stack draaide al met de gestagede code.

## Wat kon beter

De regel over `docker compose config` stond nog niet gestaged in de overlay. Ik moest zelf vaststellen dat hij na de bouw kwam, om te bepalen of het ontbreken van die test een bevinding van de bouwer is.

## Wat deed ik zelf goed

Ik voegde zeven eigen mutanten toe op regels die forge niet raakte (logregels, maker in het overzicht, rechten op API-niveau, soort bij rechten wijzigen) en noemde per mutant de falende assert. De migratie heb ik ook met data getoetst: een robottoken van vóór 0009 en een persoonlijk token bij de downgrade.

## Wat heb ik onderweg verbeterd

Mijn eerste proefscript voor de migratie liep vast op een verplichte kolom van `beheerder`. Ik heb de invoer gecorrigeerd in de scratchpad en de proef opnieuw gedraaid, zonder de gedeelde database te raken.

## Wat kan structureel beter in de opdracht

Zet in de opdracht: "Noem bij elke review welke regels in de overlay na de bouw zijn toegevoegd; een ontbrekende test op zo'n regel telt als restpunt (ernst laag) en blokkeert de review niet."
