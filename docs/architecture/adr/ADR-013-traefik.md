# ADR-013 Traefik vervangt Nginx

**Status:** Besloten door Foundation (besluit stakeholder 2026-10-31, issue #29)
**Datum:** 2026-10-31
**Versie:** v1.1.0
**Raakt:** ADR-001, ADR-002, ADR-005, ADR-008, ADR-009, ADR-010, ADR-012

## Context

Systeembeheerders draaien de applicatie naast andere diensten achter één Traefik. Traefik vervangt Nginx en neemt de controles uit `docker/nginx/` over (besluit stakeholder, issue #29).

**Aanname.** Op de host draait één gedeelde Traefik voor meer diensten. Hij vindt de containers van deze installatie via de Docker-provider en labels, over netwerken die buiten de compose bestaan. De compose bevat geen eigen Traefik, behalve lokaal in `compose.dev.yml`.

## Besluit

**Netwerken.** Op het gedeelde netwerk van Traefik zou elke dienst op de host `api:8000` rechtstreeks kunnen aanroepen, met een vervalst `X-Forwarded-For`. Traefik sluit daarom aan op twee netwerken van deze installatie. De beheerder maakt ze eenmalig aan met `docker network create --internal`; de compose noemt ze `external`.

| Netwerk | Leden | Eigenschap |
|---------|-------|-----------|
| `${INSTALLATIE}_voorkant` | Traefik, web, api | intern |
| `${INSTALLATIE}_koppeling` | Traefik (alias `traefik`), integratie | intern, subnet `KOPPELNET` |
| `achterkant` | web, api, worker, migrate, db | ongewijzigd, zonder proxy |
| `buiten` | integratie | ongewijzigd |

`integratie` bereikt alleen Traefik; `api` staat niet op `koppeling`. `integratie` start pas als `api` gezond is (`depends_on` met `service_healthy`): zolang `api` start, geeft Traefik 404, en na een mislukte eerste ronde wacht de container een uur.

**Controles.** Middlewares en routers staan als labels op `web` en `api`. Elke router noemt zijn entrypoint, anders hangt Traefik hem aan alle entrypoints.

| Controle uit Nginx | Plek onder Traefik | Proef |
|--------------------|--------------------|-------|
| TLS 1.2 en hoger, certificaat | Entrypoint `websecure`, labels `tls=true` en `tls.certresolver=${TRAEFIK_CERTRESOLVER}`; standaard TLS-opties | `openssl s_client -tls1_1` faalt, `-tls1_2` slaagt met een geldig certificaat voor `DOMEIN` |
| Doorverwijzing van 80 | Router op `web` met middleware `redirectscheme` (permanent) | `curl -I http://DOMEIN/` geeft 301 of 308 naar https |
| CSP, `nosniff`, Referrer-Policy, Permissions-Policy, HSTS, geen serverversie | Middleware `headers` op alle routers van `web` (HSTS 31536000, `customResponseHeaders.Server=""`); op `api` alleen `nosniff` | `curl -I` op `/`, op een 404 en op een 429: alle headers aanwezig, geen `Server: gunicorn` |
| Rate limit inloggen: 30 per minuut per IP, burst 20, alleen POST (ADR-001) | Eigen router `Method(POST) && (PathPrefix(/inloggen) \|\| PathPrefix(/uitnodiging))` met hogere prioriteit, middleware `ratelimit` op het verbindingsadres | 25 POST's achter elkaar: vanaf de 21e 429; 25 keer GET geeft nooit 429 |
| Rate limit API: 60 per minuut per token, burst 10 (ADR-005) | Middleware `ratelimit` met `sourceCriterion.requestHeaderName=Authorization` | 12 aanroepen in een seconde: 429 met `Retry-After`; een tweede token in dezelfde seconde krijgt 200; een nepgeheim met de prefix van het echte token remt het echte token niet (AEG-01) |
| Rate limit API per IP: 300 per minuut, burst 50 | Tweede middleware `ratelimit` op het verbindingsadres, na die per token | 60 aanroepen met willekeurige tokens vanaf `koppeling`: 429 na ongeveer 50 |
| Grens van 2 MB als JSON-413 (ADR-012) | Applicatie: `MAX_CONTENT_LENGTH` in `api` geeft de JSON al. Traefik: middleware `buffering` met `maxRequestBodyBytes` 3 MB als buitengrens, in het geheugen | 2,1 MB: 413 als JSON en één toegangsregel; 3,5 MB: 413 van Traefik |
| 1 MB algemeen, 10 MB op `/boten` (ADR-008) | Middleware `buffering` per router; de applicatie houdt `UPLOAD_MAX` | 1,5 MB op een formulier: 413; foto van 9 MB op `/boten` slaagt |
| Publieke server kent `/api/` niet | Geen router naar `api` op `websecure`; regel van `web`: `Host(DOMEIN) && !PathPrefix(/api/)` | `https://DOMEIN/api/v1/ik` geeft 404 |
| Interne server op 8081 (ADR-012) | Entrypoint `intern` op 8081, niet gepubliceerd; router `ClientIP(KOPPELNET) && PathPrefix(/api/v1/)` alleen op `intern` | Vanaf `koppeling` 200 op `/api/v1/ik`; vanaf een ander netwerk van Traefik 404; poort 8081 van buiten dicht |
| `X-Forwarded-For` overschrijven | Traefik vertrouwt geen binnenkomende `X-Forwarded-*` zonder `trustedIPs`; `PROXY_HOPS=1` blijft | Aanroep met `X-Forwarded-For: 10.203.0.99`, en ook met `X_Forwarded_For`, `X-Real-Ip` en `Forwarded`: het log van de API toont het eigen adres; een token met alleen dat adres op de whitelist krijgt 403 |
| Logformaat `zonder_code`, geen codes en zoektermen (#5, #14) | Applicatie: Gunicorn schrijft de toegangslog met een eigen loggerklasse, in hetzelfde formaat, pad zonder querystring, `/uitnodiging/...` gemaskeerd, de eigen healthcheck niet. Traefik: `observability.accesslogs=false` op elke router | Per verzoek precies één regel in de log van `web` of `api`; na een zoekopdracht en een uitnodiging staan zoekterm en code nergens, ook niet in de log van Traefik |
| Health zonder rate limit (ADR-010) | `/health/*` via de algemene router van `web`, zonder `ratelimit`; Traefik stuurt alleen naar gezonde containers | 100 keer `/health/live` zonder 429; een gestopte of startende `web` geeft 404 (besluit stakeholder 2026-10-31) |

**Versie.** Getest en vereist is `traefik:v3.7.17`. Een andere versie vraagt dat de proeven opnieuw slagen.

**Eisen aan de gedeelde Traefik.** Docker-provider met `exposedByDefault=false`, entrypoints `web` (80), `websecure` (443) en `intern` (8081, niet gepubliceerd), geen `forwardedHeaders.trustedIPs` of `insecure` op die drie, `http.aliasHeadersStrategy=delete` op die drie, aangesloten op beide netwerken, en een certresolver die certificaten bij Let's Encrypt aanvraagt (besluit stakeholder 2026-11-01). Staat er een load balancer vóór Traefik, dan gaat `PROXY_HOPS` naar 2 en krijgt alleen die het vertrouwen.

`aliasHeadersStrategy=delete` haalt een kop weg waarvan de naam een andere kop nabootst, zoals `X_Forwarded_For`. Zonder instelling laat Traefik zo'n kop ongewijzigd door en waarschuwt hij bij het starten. Gunicorn gebruikt zo'n kop niet (proef met 401 in `werk/traefik-proeven.md`), dus de botenloods is ook zonder de eis niet kwetsbaar. De eis sluit het gat voor de zekerheid: een andere versie van Gunicorn of een andere dienst achter dezelfde entrypoints kan zo'n kop wel lezen. `delete` beschermt de upstream even goed als `reject` en weigert geen verzoeken van clients van andere diensten die zulke koppen sturen.

**Nieuwe omgevingsvariabelen.** `DOMEIN` (verplicht, gelijk aan de host uit `BASIS_URL`), `INSTALLATIE` (standaard `botenloods`, voor netwerk- en routernamen, uniek per host) en `TRAEFIK_CERTRESOLVER` (verplicht voor `web` in productie). `app/config.py` controleert `DOMEIN` en `TRAEFIK_CERTRESOLVER`. `INSTALLATIE` staat alleen in compose: de applicatie gebruikt de waarde niet, en bij een verkeerde waarde start compose niet, omdat het netwerk niet bestaat. `API_URL` wordt instelbaar in de config van de integratiecontainer, standaard `http://traefik:8081/api/v1`.

**Lokaal.** `compose.dev.yml` krijgt een eigen `traefik` van dezelfde tag. De statische instellingen staan als `command` in `compose.dev.yml`, niet in een bestand: de Docker-provider krijgt de constraint `traefik.docker.network=${INSTALLATIE}_voorkant`, die interpolatie nodig heeft, en Traefik combineert een statisch bestand niet met argumenten. Zonder constraint ziet de lokale Traefik ook de containers van een tweede stack op dezelfde host, zoals die voor de screenshots. Het entrypoint `web` staat op 127.0.0.1:8080 zonder TLS, `intern` op 8081 zonder poort naar de host, en de toegangslog staat aan zoals bij een gedeelde Traefik. Compose maakt `voorkant` en `koppeling` zelf aan, beide intern. Een extra netwerk `lokaal` met uitgang geeft `traefik` en `db` hun poort op 127.0.0.1, omdat een intern netwerk geen poorten publiceert. `docker/nginx/` vervalt.

**Zekerheid.** Beide eigenschappen die Probable waren, zijn bij de bouw met een proef aangetoond (`werk/traefik-proeven.md`): `observability.accesslogs=false` per router werkt, en Traefik slaat ongezonde containers over. Een ongezonde of startende `web` heeft dan geen router meer, dus Traefik geeft 404 en geen 503. De stakeholder aanvaardde dat op 2026-10-31 (#36): het duurt alleen zolang `web` start, en een 503 vraagt extra configuratie in Traefik.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| `web` en `api` op het gedeelde netwerk van Traefik | Andere diensten bereiken `api:8000` buiten Traefik om, met een vervalst clientadres |
| Rate limit per token in Flask | Teller per Gunicorn-worker of een extra Redis (ADR-005) |
| `errors`-middleware voor een JSON-429 | Extra route; onzeker of `Retry-After` blijft |
| Toegangslog van Traefik zonder `RequestPath` | Globale instelling van de gedeelde Traefik; raakt andere diensten en ligt buiten deze installatie |

## Gevolgen

- Een 429 van Traefik heeft de tekst `Too Many Requests` met `Retry-After`, zonder `Content-Type`. `TeVeel` in `app/api/openapi.yaml` noemt daarom geen mediatype. De integratiecontainer leest alleen de status.
- Traefik geeft elke waarde van `Authorization` een eigen teller, ook headers die geen token zijn. Verzoeken zonder header delen één teller. De grens per IP blijft eronder.
- Een 429 van Traefik en een 413 boven 3 MB komen in geen enkele toegangslog (architectuur §10.2, vraag 7).
- #14 verdwijnt met de bouw: de querystring komt nooit in de log. #26 vervalt: er is geen foutlog van Nginx meer. #5 blijft open voor de foutlog van Flask. #20 blijft open: `web`, `worker` en `migrate` bereiken `api` nog via `achterkant`.
- De gedeelde Traefik leest de Docker-socket en heeft daarmee de rechten van root op de host. Dat is beheer van de host; de beheerdocumentatie raadt een socketproxy met leesrechten aan.
- Na een herstart van `web` of `api` is geen herstart van de proxy meer nodig.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.1.0 | 2026-11-01 | Bouw beschreven (issue #36): lokale Traefik met instellingen in `compose.dev.yml` en netwerk `lokaal`, `INSTALLATIE` alleen in compose, `integratie` wacht op een gezonde `api`, 429 zonder `Content-Type`, eis `aliasHeadersStrategy=delete` | Afwijkingen bij de bouw van #29 |
| v1.0.2 | 2026-11-01 | Certresolver via Let's Encrypt | Besluit stakeholder 2026-11-01 |
| v1.0.1 | 2026-10-31 | Proef health: 404 in plaats van 503 bij een ongezonde `web`; zekerheid na de proeven bij de bouw | Besluit stakeholder 2026-10-31, issue #36 |
| v1.0.0 | 2026-10-31 | Eerste versie | Besluit stakeholder 2026-10-31, issue #29 |
