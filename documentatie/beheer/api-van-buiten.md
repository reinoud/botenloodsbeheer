# API van buiten

**Versie:** v1.0.0
**Datum:** 2026-11-03
**Bronnen:** ADR-005, ADR-012, ADR-013, `compose.api-extern.yml`, `app/api/openapi.yaml`

Standaard is de API alleen bereikbaar voor de integratiecontainer, via het entrypoint `intern` van Traefik. Een persoonlijk token of een koppeling buiten de installatie heeft de API op `https://DOMEIN/api/v1` nodig. Die zet je bewust open met `compose.api-extern.yml`. Zonder dat bestand geeft `https://DOMEIN/api/v1/ik` 404.

## Openzetten

1. Kies de adressen die de API van buiten mogen bereiken, zoals het vaste adres van een kantoor of een server met een koppeling. Zet ze in `.env` als `API_EXTERN_BRONNEN`, adressen of reeksen in CIDR-notatie met komma's ertussen:

   ```sh
   API_EXTERN_BRONNEN=203.0.113.0/24,2001:db8::/32
   ```

2. Start met het extra bestand:

   ```sh
   docker compose -f docker-compose.yml -f compose.api-extern.yml up -d api
   ```

   Gebruik dezelfde `-f`-opties bij elk volgend `up`, ook na een update. Laat je het bestand weg, dan verdwijnt de route en is de API weer alleen intern.

3. Controleer vanaf een adres uit `API_EXTERN_BRONNEN` met een token: `curl -H "Authorization: Bearer blb_..." https://DOMEIN/api/v1/ik` geeft 200. Vanaf een ander adres geeft dezelfde aanroep 403.

Ontbreekt `API_EXTERN_BRONNEN` of is hij leeg, dan start compose met dit bestand niet en meldt hij welke variabele ontbreekt.

## Twee whitelists

Een aanroep van buiten gaat langs twee controles. Traefik laat alleen adressen uit `API_EXTERN_BRONNEN` door en geeft anders 403; zo'n weigering komt in geen log van de applicatie. Daarna toetst de applicatie de whitelist van het token, op het adres dat Traefik vaststelt. Een adres dat de client zelf in een kop als `X-Forwarded-For` meestuurt, telt niet. Een token buiten zijn whitelist krijgt 401, met een regel `api.geweigerd` in het technische log.

Staat er een load balancer vóór Traefik, dan ziet Traefik het adres van de load balancer. Dan toetsen `externtoegang` en `iprem` dat adres, en niet dat van de client. Zet dan `PROXY_HOPS=2`, anders toetst ook de applicatie de whitelist van het token op dat adres ([installatie](installatie.md)). Deze opzet is niet getest: `iprem` geldt ook voor de interne route van de integratiecontainer, dus een andere `ipStrategy` op `iprem` verandert ook die rate limit (#54).

Een persoonlijk token zonder whitelist werkt vanaf elk adres in `API_EXTERN_BRONNEN`. `0.0.0.0/0,::/0` opent de API voor elk adres; dan begrenst alleen de whitelist van het token. Kies dat alleen als elk token dat buiten gebruikt wordt een whitelist heeft.

De gedeelde Traefik moet aan dezelfde eisen voldoen als bij de installatie, ook op `websecure`: geen `forwardedHeaders.trustedIPs` en `aliasHeadersStrategy=delete` ([installatie](installatie.md)). Anders kan een client zijn adres vervalsen.

## Rate limit

Van buiten gelden dezelfde grenzen als intern: 60 aanroepen per minuut per token, met een burst van 10, en 300 per minuut per adres. Daarboven antwoordt Traefik met 429 en `Retry-After`. Traefik telt per route, dus een token dat zowel intern als van buiten wordt gebruikt, krijgt op elk van beide 60 per minuut.

## De leesaanroepen

Elke aanroep geeft de hele lijst, zonder filters of paginering. Het recht `persoonsgegevens` voegt velden toe: zonder dat recht ontbreken adres, telefoon en e-mail, en bij leden ook `lid_sinds` en `opzegdatum`. Een veld zonder waarde is `null`. De volledige beschrijving met voorbeelden staat in `app/api/openapi.yaml`.

| Aanroep | Recht | Velden |
|---------|-------|--------|
| `GET /api/v1/plaatsen` | `plaatsen:lezen` | `code`, `rek`, `clubplaats`, `bootsoorten`, `boot` (`id`, `naam`) |
| `GET /api/v1/boten` | `boten:lezen` | `id`, `naam`, `bootsoort`, `plaats`, `eigenaar` (`lidnummer`, `naam`; `null` bij een clubboot) |
| `GET /api/v1/leden` | `leden:lezen` | `lidnummer`, `naam`, `oud_lid` |
| `GET /api/v1/wachtlijst` | `wachtlijst:lezen` | `bootsoort`, `boot`, `eigenaar`, `aangemeld_op`; zonder boten van oud-leden |

Een voorbeeld met een nep-token:

```sh
curl -s -H "Authorization: Bearer blb_VOORBEELDVOORBEELDVOORBEELDVOORBEELDVOORBEELDVOORBEELDVOORBEE" \
  https://DOMEIN/api/v1/boten
# [{"bootsoort": "Kajak", "eigenaar": {"lidnummer": "1001", "naam": "Anna Voorbeeld"},
#   "id": 7, "naam": "Zeemeeuw", "plaats": "A01"}]
```

## Weer dichtzetten

Start zonder `compose.api-extern.yml`: `docker compose up -d api`. Trek daarna de tokens in die alleen van buiten werden gebruikt, op het scherm Tokens.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.0.0 | 2026-11-03 | Eerste versie | BLB-042, slice 10 |
