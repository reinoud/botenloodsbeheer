# ADR-013 Traefik vervangt Nginx

**Status:** Besloten door Foundation (besluit stakeholder 2026-10-31, issue #29)
**Datum:** 2026-10-31
**Versie:** v1.5.1
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
| 1 MB algemeen; 10 MB voor foto en logo in de applicatie, 25 MB als buitengrens in Traefik op `/boten` en `/instellingen/logo` (ADR-008, besluit stakeholder 2026-11-10) | Middleware `buffering` (`25mb`) per router; de applicatie houdt `UPLOAD_MAX` en geeft daarboven een melding | 1,5 MB op een formulier: 413; foto van 9 MB op `/boten` slaagt; 15 MB: melding van de applicatie; 30 MB: 413 van Traefik |
| Publieke server kent `/api/` niet | Geen router naar `api` op `websecure`; regel van `web`: `Host(DOMEIN) && !PathPrefix(/api/)` | `https://DOMEIN/api/v1/ik` geeft 404 |
| Interne server op 8081 (ADR-012) | Entrypoint `intern` op 8081, niet gepubliceerd; router `ClientIP(KOPPELNET) && PathPrefix(/api/v1/)` alleen op `intern` | Vanaf `koppeling` 200 op `/api/v1/ik`; vanaf een ander netwerk van Traefik 404; poort 8081 van buiten dicht |
| `X-Forwarded-For` overschrijven | Traefik vertrouwt geen binnenkomende `X-Forwarded-*` zonder `trustedIPs`; `PROXY_HOPS=1` blijft | Aanroep met `X-Forwarded-For: 10.203.0.99`, en ook met `X_Forwarded_For`, `X-Real-Ip` en `Forwarded`: het log van de API toont het eigen adres; een token met alleen dat adres op de whitelist krijgt 403 |
| Logformaat `zonder_code`, geen codes en zoektermen (#5, #14) | Applicatie: Gunicorn schrijft de toegangslog met een eigen loggerklasse, in hetzelfde formaat, pad zonder querystring, `/uitnodiging/...` gemaskeerd, een pad met procentcodering tot het eerste `%` (#72), de eigen healthcheck niet. Traefik: `observability.accesslogs=false` op elke router | Per verzoek precies één regel in de log van `web` of `api`; na een zoekopdracht en een uitnodiging staan zoekterm en code nergens, ook niet in de log van Traefik |
| Health zonder rate limit (ADR-010) | `/health/*` via de algemene router van `web`, zonder `ratelimit`; Traefik stuurt alleen naar gezonde containers | 100 keer `/health/live` zonder 429; een gestopte of startende `web` geeft 404 (besluit stakeholder 2026-10-31) |

**API van buiten (BLB-042).** `compose.api-extern.yml` voegt alleen labels toe aan `api`, dat al op `voorkant` staat. Zonder het bestand blijft de proef "`https://DOMEIN/api/v1/ik` geeft 404" gelden.

| Onderdeel | Waarde |
|-----------|--------|
| Router `${INSTALLATIE}-api-extern` | `Host(DOMEIN) && PathPrefix(/api/v1/)` op `websecure`, `tls=true` met `TRAEFIK_CERTRESOLVER`, `priority` 2000, `observability.accesslogs=false` |
| Middlewares, in deze volgorde | `nosniff`, `externtoegang`, `tokenrem`, `iprem`, `3mb` |
| `externtoegang` | `ipallowlist.sourcerange=${API_EXTERN_BRONNEN:?}`, zonder `ipStrategy`, dus op het verbindingsadres |
| `API_EXTERN_BRONNEN` | Nieuw, verplicht met dit bestand, CIDR-reeksen met komma's; alleen compose leest hem |

De whitelist werkt in twee lagen. Traefik laat alleen adressen uit `API_EXTERN_BRONNEN` door en geeft anders 403, zonder regel in het log van de applicatie. Daarna toetst de applicatie de whitelist van het token op het adres dat Traefik vaststelt; de eisen aan de gedeelde Traefik gelden ook voor `websecure`, dus een meegestuurde kop telt niet. De eerste laag begrenst een persoonlijk token met een lege whitelist, en laat de installatie bewust kiezen hoe ver de API naar buiten gaat; `0.0.0.0/0,::/0` is zo'n keuze.

De rate limit gebruikt dezelfde middlewares als `intern`, dus dezelfde grenzen. Traefik houdt per router een eigen teller (Probable): een token op beide entrypoints krijgt per entrypoint 60 per minuut. Verkeer van buiten loopt altijd via Traefik; de route over `achterkant` blijft, dus #20 blijft open.

Proeven met een losse Traefik: zonder het bestand 404; met het bestand 200 vanaf een adres in `API_EXTERN_BRONNEN` en in de whitelist van het token; 403 vanaf een adres buiten `API_EXTERN_BRONNEN`; 401 vanaf een adres binnen de bronnen maar buiten de tokenwhitelist, ook met `X-Forwarded-For` op een adres in die whitelist; 429 na 11 aanroepen in een seconde; compose start niet zonder `API_EXTERN_BRONNEN`. Forge schrijft `documentatie/beheer/api-van-buiten.md`.

**Versie.** Getest en vereist is `traefik:v3.7.17`. Een andere versie vraagt dat de proeven opnieuw slagen.

**Eisen aan de gedeelde Traefik.** Docker-provider met `exposedByDefault=false`, entrypoints `web` (80), `websecure` (443) en `intern` (8081, niet gepubliceerd), geen `forwardedHeaders.trustedIPs` of `insecure` op die drie, `http.aliasHeadersStrategy=delete` op die drie, aangesloten op beide netwerken, en een certresolver die certificaten bij Let's Encrypt aanvraagt (besluit stakeholder 2026-11-01).

`aliasHeadersStrategy=delete` haalt een kop weg waarvan de naam een andere kop nabootst, zoals `X_Forwarded_For`. Zonder instelling laat Traefik zo'n kop ongewijzigd door en waarschuwt hij bij het starten. Gunicorn gebruikt zo'n kop niet (proef met 401 in `werk/traefik-proeven.md`), dus de botenloods is ook zonder de eis niet kwetsbaar. De eis sluit het gat voor de zekerheid: een andere versie van Gunicorn of een andere dienst achter dezelfde entrypoints kan zo'n kop wel lezen. `delete` beschermt de upstream even goed als `reject` en weigert geen verzoeken van clients van andere diensten die zulke koppen sturen.

**Load balancer vóór Traefik (issue #54).** De load balancer geeft het clientadres door met het PROXY protocol. De gedeelde Traefik vertrouwt dat alleen van de load balancer: `--entrypoints.websecure.proxyprotocol.trustedips=<adressen van de load balancer>`, en op `web` als die ook poort 80 doorstuurt. Traefik gebruikt het clientadres dan als verbindingsadres. `externtoegang`, `tokenrem`, `iprem`, `inlogrem` en de whitelist van het token toetsen zo de client, zonder labelwijziging. `PROXY_HOPS` blijft 1. Geen nieuwe omgevingsvariabele: de instelling hoort bij de gedeelde Traefik. Dit is geen optie op het entrypoint als eis van de botenloods (zie de alternatieven): de load balancer staat vóór de hele gedeelde Traefik, en zonder de optie leest Traefik de PROXY-kop niet en werkt geen dienst op `websecure`. De load balancer zet zelf op elke verbinding een PROXY-kop, en `trustedips` bevat alleen zijn exacte adressen; anders kan een client zijn eigen adres opgeven (review aegis).

`api` en `api-extern` blijven dezelfde middlewares delen. De instelling staat alleen op de entrypoints waarop de load balancer aansluit, nooit op `intern`, dus de interne rate limit verandert er niet door. Een PROXY-kop van een ander adres dan de load balancer telt niet; Traefik toetst dan het adres van de verbinding (proef `tests/proxy/draai.sh`).

Bewust ontbreken `forwardedHeaders.trustedIPs`, `forwardedHeaders.insecure` en `proxyProtocol.insecure` op elk entrypoint, en `ipStrategy` (`depth`, `excludedIPs`, `ipv6Subnet`) op elke middleware. Een load balancer met alleen `X-Forwarded-For` wordt niet ondersteund (besluit stakeholder 2026-11-05). `PROXY_HOPS=2` breekt de interne route: daar staat één adres in `X-Forwarded-For`, dus de applicatie toetst het token van de integratiecontainer op het adres van Traefik.

Proef (losse Traefik met de optie op `websecure`, een client als load balancer): 200, 401 en 403 volgen het clientadres in de PROXY-kop; elke client heeft een eigen teller in `iprem`; een PROXY-kop van een ander adres geeft geen 200; op `intern` geeft één adres 429 na ongeveer 50 aanroepen en krijgt een tweede adres in dezelfde seconde 401. Zonder de optie slagen de bestaande proeven ongewijzigd.

**Gecodeerd pad (issue #65, PRB-01).** Traefik kiest de router op het pad zoals het binnenkomt, en `%2F` blijft gecodeerd. `POST /%2Finloggen` valt daardoor onder de router `web` zonder rem. Werkzeug decodeert het pad, voegt de dubbele schuine streep samen en verwerkt de inlog. Elke route naar `api` draagt de rate limits, ook met `compose.api-extern.yml`; een API-pad met codering valt onder `web`.

| Laag | Plek | Gedrag |
|------|------|--------|
| Applicatie, verplicht | `create_app`: `before_request` op de app, dus voor `web` en `api` | `abort(400)` als het pad in `RAW_URI` (zonder querystring) een `%` bevat |
| Traefik, aanbevolen | Entrypoints `web`, `websecure` en `intern` in het voorbeeld en in `compose.dev.yml` | `http.encodedcharacters.allowencodedslash`, `allowencodedbackslash`, `allowencodednullcharacter` en `allowencodedpercent` op `false`: 400 van Traefik |

De applicatielaag beschermt elke installatie vanzelf, ook achter een bestaande Traefik zonder de opties. Geen route van de botenloods heeft procentcodering in het pad nodig: padparameters zijn getallen of tokens. Een nieuwe route met vrije tekst in het pad vraagt een nieuw besluit. De opties op het entrypoint zijn geen eis aan de gedeelde Traefik, omdat ze ook andere diensten op die entrypoints raken. `allowEncodedSemicolon`, `allowEncodedQuestionMark` en `allowEncodedHash` blijven bewust aan: de applicatielaag weigert ze al, aegis vond er geen omweg mee, en elke extra weigering raakt die andere diensten ook (review #65).

Proef (losse Traefik v3.7.17, Gunicorn met Flask, lege bucket): `/%2Finloggen`, `/%2finloggen/code`, `/%2Fuitnodiging/abc`, `%5C`, `%00`, `%252F`, `/.%2F` en `GET /api%2Fv1/ik` geven 400 met elk van beide lagen; zonder lagen verwerkt Flask de inlog. Traefik decodeert `%2E` en gecodeerde letters zelf, dus `/%69nloggen` krijgt 429.

**Nieuwe omgevingsvariabelen.** `DOMEIN` (verplicht, gelijk aan de host uit `BASIS_URL`), `INSTALLATIE` (standaard `botenloods`, voor netwerk- en routernamen, uniek per host) en `TRAEFIK_CERTRESOLVER` (verplicht voor `web` in productie). `app/config.py` controleert `DOMEIN` en `TRAEFIK_CERTRESOLVER`. `INSTALLATIE` staat alleen in compose: de applicatie gebruikt de waarde niet, en bij een verkeerde waarde start compose niet, omdat het netwerk niet bestaat. `API_URL` wordt instelbaar in de config van de integratiecontainer, standaard `http://traefik:8081/api/v1`.

**Lokaal.** `compose.dev.yml` krijgt een eigen `traefik` van dezelfde tag. De statische instellingen staan als `command` in `compose.dev.yml`, niet in een bestand: de Docker-provider krijgt de constraint `traefik.docker.network=${INSTALLATIE}_voorkant`, die interpolatie nodig heeft, en Traefik combineert een statisch bestand niet met argumenten. Zonder constraint ziet de lokale Traefik ook de containers van een tweede stack op dezelfde host, zoals die voor de screenshots. Het entrypoint `web` staat op 127.0.0.1:8080 zonder TLS, `intern` op 8081 zonder poort naar de host, en de toegangslog staat aan zoals bij een gedeelde Traefik. `aliasHeadersStrategy` staat lokaal niet: de eis geldt voor de gedeelde Traefik, en de lokale Traefik draait alleen op 127.0.0.1. Compose maakt `voorkant` en `koppeling` zelf aan, beide intern. Een extra netwerk `lokaal` met uitgang geeft `traefik` en `db` hun poort op 127.0.0.1, omdat een intern netwerk geen poorten publiceert. `docker/nginx/` vervalt.

**Zekerheid.** Beide eigenschappen die Probable waren, zijn bij de bouw met een proef aangetoond (`werk/traefik-proeven.md`): `observability.accesslogs=false` per router werkt, en Traefik slaat ongezonde containers over. Een ongezonde of startende `web` heeft dan geen router meer, dus Traefik geeft 404 en geen 503. De stakeholder aanvaardde dat op 2026-10-31 (#36): het duurt alleen zolang `web` start, en een 503 vraagt extra configuratie in Traefik.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| `web` en `api` op het gedeelde netwerk van Traefik | Andere diensten bereiken `api:8000` buiten Traefik om, met een vervalst clientadres |
| Rate limit per token in Flask | Teller per Gunicorn-worker of een extra Redis (ADR-005) |
| `errors`-middleware voor een JSON-429 | Extra route; onzeker of `Retry-After` blijft |
| Router `inloggen` ook op de gecodeerde vorm laten matchen | De regex moet de normalisatie van Werkzeug volgen |
| `url_map.merge_slashes=False` | Werkt niet na het aanmaken van de `Map` (proef); alleen met een eigen `Map`-klasse |
| Opties op het entrypoint als eis | Raakt andere diensten op de gedeelde Traefik |
| Eigen `iprem` en `externtoegang` met `ipStrategy.depth` voor een load balancer | Vraagt `trustedIPs` op `websecure` en een `PROXY_HOPS` per route, terwijl `api` er één heeft |
| Toegangslog van Traefik zonder `RequestPath` | Globale instelling van de gedeelde Traefik; raakt andere diensten en ligt buiten deze installatie |

## Gevolgen

- Een 429 van Traefik heeft de tekst `Too Many Requests` met `Retry-After`, zonder `Content-Type`. `TeVeel` in `app/api/openapi.yaml` noemt daarom geen mediatype. De integratiecontainer leest alleen de status.
- Traefik geeft elke waarde van `Authorization` een eigen teller, ook headers die geen token zijn. Verzoeken zonder header delen één teller. De grens per IP blijft eronder.
- Een 429 van Traefik en een 413 boven 3 MB komen in geen enkele toegangslog (architectuur §10.2, vraag 7).
- #14 verdwijnt met de bouw: de querystring komt nooit in de log. #26 vervalt: er is geen foutlog van Nginx meer. #5 blijft open voor de foutlog van Flask. #20 blijft open: `web`, `worker` en `migrate` bereiken `api` nog via `achterkant`.
- De gedeelde Traefik leest de Docker-socket en heeft daarmee de rechten van root op de host. Dat is beheer van de host; de beheerdocumentatie raadt een socketproxy met leesrechten aan.
- Na een herstart van `web` of `api` is geen herstart van de proxy meer nodig.
- De middleware `25mb` buffert een upload op `/boten` en `/instellingen/logo` tot 25 MB in het geheugen van de gedeelde Traefik, ook zonder inlog. In het slechtste geval houdt elke open verbinding 25 MB vast zolang de upload duurt; de rate limit begrenst het aantal verzoeken, niet het aantal open verbindingen. Voor deze installatie aanvaardbaar; een lager geheugendeel vraagt een schrijfbare tijdelijke map in de gedeelde Traefik (review Aegis bij #190).

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.5.1 | 2026-11-11 | Voorbeeld van de gedeelde Traefik: images op een digest, onder Dependabot, `read_only`, `cap_drop` en `no-new-privileges` | Issue #230, AEG-08 |
| v1.5.0 | 2026-11-10 | Buitengrens van 25 MB op `/boten` en `/instellingen/logo` (middleware `25mb`), de applicatie houdt 10 MB | Besluit stakeholder 2026-11-10, issue #190 |
| v1.4.2 | 2026-11-05 | Verschil met de verworpen opties op het entrypoint; eisen aan load balancer en `trustedips` | Review aegis, issue #54 |
| v1.4.1 | 2026-11-05 | Herkomst van het besluit over `X-Forwarded-For`; proef bevestigt `trustedips` | Besluit stakeholder, issue #54 |
| v1.4.0 | 2026-11-05 | Load balancer via PROXY protocol op het entrypoint; middlewares blijven gedeeld, `PROXY_HOPS=2` vervalt | Issue #54 |
| v1.3.2 | 2026-11-03 | Toegangslog: pad met procentcodering afgekapt bij het eerste `%` | Issue #72 |
| v1.3.1 | 2026-11-03 | Waarom drie opties voor gecodeerde tekens ontbreken | Review aegis, issue #65 |
| v1.3.0 | 2026-11-03 | Gecodeerd pad: 400 in de applicatie, opties voor gecodeerde tekens aanbevolen op de entrypoints, proef | Securityronde na slice 11, PRB-01, issue #65 |
| v1.2.0 | 2026-11-03 | API van buiten: router, `API_EXTERN_BRONNEN`, rate limit, proeven | Ontwerp slice 10, issue #51 |
| v1.1.1 | 2026-11-01 | Lokaal: `aliasHeadersStrategy` alleen bij de gedeelde Traefik | Review Sentinel, issue #36 |
| v1.1.0 | 2026-11-01 | Bouw beschreven (issue #36): lokale Traefik met instellingen in `compose.dev.yml` en netwerk `lokaal`, `INSTALLATIE` alleen in compose, `integratie` wacht op een gezonde `api`, 429 zonder `Content-Type`, eis `aliasHeadersStrategy=delete` | Afwijkingen bij de bouw van #29 |
| v1.0.2 | 2026-11-01 | Certresolver via Let's Encrypt | Besluit stakeholder 2026-11-01 |
| v1.0.1 | 2026-10-31 | Proef health: 404 in plaats van 503 bij een ongezonde `web`; zekerheid na de proeven bij de bouw | Besluit stakeholder 2026-10-31, issue #36 |
| v1.0.0 | 2026-10-31 | Eerste versie | Besluit stakeholder 2026-10-31, issue #29 |
