# API van buiten

**Versie:** v1.2.0
**Datum:** 2026-11-10
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

Fouten van de applicatie zijn JSON met één veld `fout`, ook bij een onbekend pad (404), een methode die het pad niet kent (405) en een NUL-teken in de querystring (400). Een weigering door Traefik (403, 429, een te groot verzoek of een pad met `%2F`, `%5C`, `%25` of `%00`, 400) is platte tekst of leeg; lees daar alleen de status.

Staat er een load balancer vóór Traefik, dan geeft die het clientadres door met het PROXY protocol. Zet in de gedeelde Traefik `--entrypoints.websecure.proxyprotocol.trustedips=<adressen van de load balancer>`, en op `web` als de load balancer ook poort 80 doorstuurt. Traefik gebruikt dan het adres uit de PROXY-kop, dus `externtoegang`, `iprem` en de whitelist van het token toetsen de client. Elke client heeft een eigen teller in `iprem`. `PROXY_HOPS` blijft 1 en de labels blijven gelijk. Zet de optie alleen als de load balancer op elke verbinding zelf een PROXY-kop zet (zoals `send-proxy`), en alleen met de exacte adressen van de load balancer (`/32` of `/128`), nooit met een subnet waarin ook andere machines staan. Anders kan een client zelf een PROXY-kop sturen en elk adres opgeven; dan omzeilt hij `externtoegang`, `iprem` en de rem op inloggen. Zet de optie nooit op `intern`: daar komt de integratiecontainer binnen, en daar blijft de rate limit zoals hij is. Een PROXY-kop van een ander adres dan de load balancer telt niet; Traefik toetst dan het adres van de verbinding. Een load balancer die alleen `X-Forwarded-For` meestuurt, wordt niet ondersteund. `tests/proxy/draai.sh` toetst deze opzet in een tweede ronde (#54).

Een persoonlijk token zonder whitelist werkt vanaf elk adres in `API_EXTERN_BRONNEN`. `0.0.0.0/0,::/0` opent de API voor elk adres; dan begrenst alleen de whitelist van het token. Kies dat alleen als elk token dat buiten gebruikt wordt een whitelist heeft.

De gedeelde Traefik moet aan dezelfde eisen voldoen als bij de installatie, ook op `websecure`: geen `forwardedHeaders.trustedIPs` of `proxyProtocol.insecure`, en `aliasHeadersStrategy=delete` ([installatie](installatie.md)). Anders kan een client zijn adres vervalsen.

## Rate limit

Van buiten gelden dezelfde grenzen als intern: 60 aanroepen per minuut per token, met een burst van 10, en 300 per minuut per adres. Daarboven antwoordt Traefik met 429 en `Retry-After`. Traefik telt per route, dus een token dat zowel intern als van buiten wordt gebruikt, krijgt op elk van beide 60 per minuut.

## Proef na een wijziging

`tests/proxy/draai.sh` toetst met een losse Traefik en de echte `api` 200, 401 met vervalste koppen, 403, 429 en 404 zonder het bestand. Draai het na elke wijziging aan de labels van `api`, aan `compose.api-extern.yml` of aan de eisen aan Traefik. Het is een proef voor ontwikkelaars: hij vraagt een checkout van de repository en een lokaal image `botenloods-app`, en toetst een eigen losse Traefik, niet de gedeelde.

## De leesaanroepen

Elke aanroep geeft de hele lijst, zonder filters of paginering. De applicatie bewaart geen adres, telefoon of e-mail van leden en levert ze dus niet. Een veld zonder waarde is `null`. De volledige beschrijving met voorbeelden staat in `app/api/openapi.yaml`.

| Aanroep | Recht | Velden |
|---------|-------|--------|
| `GET /api/v1/plaatsen` | `plaatsen:lezen` | `code` (de aanduiding, zoals `A/1/1`), `rek`, `clubplaats`, `bootsoorten`, `boot` (`id`, `naam`) |
| `GET /api/v1/boten` | `boten:lezen` | `id`, `naam`, `bootsoort`, `plaats`, `eigenaar` (`lidnummer`, `naam`; `null` bij een clubboot of een onbekende eigenaar), `clubboot` (`true` bij een clubboot; zo onderscheid je een clubboot van een onbekende eigenaar) |
| `GET /api/v1/leden` | `leden:lezen` | `lidnummer`, `naam`, `oud_lid`, `lid_sinds`, `opzegdatum` |
| `GET /api/v1/wachtlijst` | `wachtlijst:lezen` | `bootsoort`, `boot`, `eigenaar`, `aangemeld_op`; zonder boten van oud-leden; `eigenaar` is `null` bij een onbekende eigenaar |

Een voorbeeld met een nep-token:

```sh
curl -s -H "Authorization: Bearer blb_VOORBEELDVOORBEELDVOORBEELDVOORBEELDVOORBEELDVOORBEELDVOORBEE" \
  https://DOMEIN/api/v1/boten
# [{"bootsoort": "Kajak", "eigenaar": {"lidnummer": "1001", "naam": "Anna Voorbeeld"},
#   "clubboot": false, "id": 7, "naam": "Zeemeeuw", "plaats": "A/1/1"}]
```

## Weer dichtzetten

Start zonder `compose.api-extern.yml`: `docker compose up -d api`. Trek daarna de tokens in die alleen van buiten werden gebruikt, op het scherm Tokens.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.0.0 | 2026-11-03 | Eerste versie | BLB-042, slice 10 |
| v1.1.0 | 2026-11-05 | Proef met een losse Traefik | Issue #53 |
| v1.2.0 | 2026-11-10 | Boten krijgt `clubboot`; `eigenaar` is ook `null` bij een onbekende eigenaar | Issues #204 en #212 |
