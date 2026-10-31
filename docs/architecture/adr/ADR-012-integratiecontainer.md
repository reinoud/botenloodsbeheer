# ADR-012 Integratiecontainer en interne API

**Status:** Besloten door Foundation (besluiten stakeholder 2026-10-31)
**Datum:** 2026-10-31
**Versie:** v1.0.0
**Stories:** BLB-006, BLB-007, BLB-008, BLB-009, BLB-029 tot en met BLB-035, BLB-037

## Context

Een aparte, vervangbare container doet alle imports en exports: leden ophalen en het aantal boten per lid en per bootsoort terugschrijven. Hij praat alleen met de API, over het interne netwerk van compose. De API staat standaard aan, is niet vanaf internet bereikbaar en heeft als standaardwhitelist het interne netwerk (intake, besluiten 2026-10-31). Terugschrijven blijft voorbereid maar uit (overlay §5).

## Besluit

**Containers en netwerken.** Er komen twee diensten bij. `api` draait het applicatie-image met `DIENST=api` en alleen de blueprint `/api/v1`, die `web` niet meer registreert. Alleen de rol `botenloods_api` maakt leden aan en werkt ze bij; `web` houdt leesrecht op `lid`. `integratie` is een eigen image uit `integratie/`, zonder applicatiecode.

| Netwerk | Leden | Eigenschap |
|---------|-------|-----------|
| `voorkant` | nginx | Poort 443 en 80 naar buiten |
| `achterkant` | nginx, web, api, worker, migrate, db | `internal: true` |
| `koppeling` | nginx, integratie | `internal: true`, vast subnet `KOPPELNET` (standaard `10.203.0.0/24`) |
| `buiten` | integratie | Uitgaand verkeer naar e-boekhouden |

Nginx krijgt een tweede, niet gepubliceerde server op poort 8081, die alleen `/api/v1/` doorstuurt naar `api`. De publieke server op 443 kent geen route naar `api`. Zo gelden de rate limits en de overschreven `X-Forwarded-For` uit ADR-005 ongewijzigd, en bereikt `integratie` `api` en `db` niet rechtstreeks.

Wie de API op internet wil, voegt bewust `compose.api-extern.yml` toe; dat bestand komt pas met een story die erom vraagt (architectuur §10.2, vraag 5).

**Aanroepen.** Het contract staat in `app/api/openapi.yaml`. De integratiecontainer gebruikt alleen deze vijf aanroepen.

| Aanroep | Recht | Argumenten | Terugkeerwaarde |
|---------|-------|------------|-----------------|
| `GET /api/v1/ik` | elk geldig token | geen | 200 `{"token": naam, "rechten": [...], "verloopt_op": datum}` |
| `GET /api/v1/leden/importverzoek` | `leden:importeren` | geen | 200 `{"aangevraagd": true}` of `{"aangevraagd": false}` |
| `PUT /api/v1/leden` | `leden:importeren` | `{"leden": [record, ...]}`, altijd de volledige lijst; record: `lidnummer`, `naam`, `adres`, `telefoon`, `email`, `lid_sinds`, `opzegdatum` (datums `JJJJ-MM-DD`) | 200 `{"ontvangen", "nieuw", "bijgewerkt", "uit_bron", "ongeldig", "overgeslagen"}`; 409 bij de veiligheidsgrens of een lopende import; 413 boven 2 MB; 422 als `leden` geen lijst is of meer dan 5000 records heeft |
| `POST /api/v1/leden/import-mislukt` | `leden:importeren` | `{"reden": ...}`, één van `bron_onbereikbaar`, `bron_onleesbaar`, `bron_geweigerd` | 201; andere reden 422 |
| `GET /api/v1/bootaantallen` | `bootaantallen:lezen` | geen | 200 `[{"lidnummer", "aantallen": {bootsoort: aantal}}]`, voor elk lid elke bootsoort, ook 0 |

**Regels aan de kant van de API.** `PUT /api/v1/leden` roept `domein/leden.synchroniseer` aan met de ontvangen lijst als bron en het token als actor. Alle regels uit ADR-004 gelden daardoor ongewijzigd: validatie per record zonder de inhoud te loggen, de veiligheidsgrens van de helft, geen nieuw lid met een opzegdatum van meer dan 5 jaar geleden, `uit_bron_op` voor een lid dat in de lijst ontbreekt, boten van oud-leden van de wachtlijst, en een logregel per lid. Een advisory lock voorkomt twee imports tegelijk. Elke import en elke gemelde fout is een run in `taakrun`; een open verzoek van een beheerder krijgt de uitkomst van de eerstvolgende import. De reden bij een fout komt uit een vaste lijst, zodat geen tekst van buiten op de statuspagina komt.

**Integratiecontainer.** Een lus van 60 seconden: vraag het importverzoek op, en importeer bij een verzoek of na `SYNC_TIJDSTIP` als die dag nog geen import slaagde. Na een fout hooguit één nieuwe poging per uur. De bron zit achter de interface uit ADR-004 (`haal_leden`, `schrijf_bootaantallen`), met een stub die een JSON-bestand leest. `schrijf_bootaantallen` gooit `NietBeschikbaar`; er draait geen taak die terugschrijft. De container draait zonder root, alleen-lezen, met alleen de standaardbibliotheek van Python.

**Token en aanmelden.** De integratiecontainer krijgt een robottoken met alleen `leden:importeren` en `bootaantallen:lezen`. Het eerste token ontstaat met de CLI in `web`: `flask token robot <naam> --recht ... [--whitelist CIDR] [--dagen N]`. De whitelist is standaard `KOPPELNET`, de geldigheid standaard 365 dagen en hooguit 3 jaar. De CLI toont het token één keer en schrijft een logregel met actor `cli`. De beheerder zet het in `secrets/api_token` (mode 0600); compose levert dat als secret op `/run/secrets/api_token` (`API_TOKEN_FILE`). De container leest het bij elke run opnieuw, dus een nieuw token vraagt geen herstart. Zonder token meldt de container dat in zijn log en wacht een minuut.

**Beheerdocumentatie.** Forge schrijft `docs/beheer/integratiecontainer.md`: token maken en instellen, de vijf aanroepen met voorbeeldcode, en wat een eigen container moet doen.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| API in `web`, met een blokkade op `/api/` in Nginx | `web` staat aan internet en zou leden mogen schrijven; de scheiding in de database verdwijnt |
| Integratiecontainer rechtstreeks naar `api:8000` | Geen rate limit en een clientadres dat de whitelist niet betrouwbaar maakt |
| Import per lid (`POST` en `PATCH`) | Een verdwenen lid is dan niet te herkennen, en de veiligheidsgrens werkt niet |

## Gevolgen

- `app/ledenbron/` en de synchronisatie in de worker verdwijnen (ADR-004, ADR-007).
- Er zijn vier databaserollen: eigenaar, web, api en taken. `integratie` heeft geen databaserol.
- Een vervangende container kent alleen de vijf aanroepen; een halve lijst houdt de veiligheidsgrens tegen.
- Na een handmatig verzoek begint de import binnen een minuut.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.0.0 | 2026-10-31 | Eerste versie | Besluiten stakeholder 2026-10-31 |
