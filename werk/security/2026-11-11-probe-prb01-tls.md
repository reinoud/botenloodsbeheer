# Proef PRB-01 met TLS op websecure (#237)

**Datum:** 2026-11-11
**Agent:** probe
**Commit:** 688c407 (main), gelezen met `git show main:<pad>`; de werkmap stond op een andere branch en is niet gewijzigd
**Normen:** ADR-013 (gecodeerd pad, rate limit inloggen); overlay §4, Security en proxy

## Oordeel

PRB-01 is ook met TLS opgelost. Op het entrypoint `websecure` geeft Traefik zelf 400 op elk pad met `%2F`, `%5C`, `%25` of `%00`, ook als de rate limit al 429 geeft. Geen van die aanroepen bereikt de upstream. Het gedrag is gelijk aan dat op `web` zonder TLS. Een mutant zonder de opties voor gecodeerde tekens laat zien dat de proef een omzeiling wel vangt: daar geeft de upstream 200 boven de grens, met en zonder TLS. Er komt geen nieuw issue.

## Opzet

Eigen compose-project `prb237` met twee interne netwerken (`prb237_voorkant`, `prb237_klant`), zonder gepubliceerde poorten. De gedeelde stack `botenloods-*` is niet gebruikt.

- **Traefik** v3.7.17 met hetzelfde digest als `compose.dev.yml:52` (`sha256:30ff6249…`). Entrypoints `web` (:8080), `websecure` (:8443) en `intern` (:8081). Per entrypoint `aliasheadersstrategy=delete` en de vier opties `encodedcharacters.allowencodedslash`, `allowencodedbackslash`, `allowencodednullcharacter` en `allowencodedpercent` op `false`, zoals in `documentatie/beheer/voorbeelden/traefik/compose.yml`. Docker-provider met `exposedbydefault=false` en een constraint op `prb237_voorkant`. Geen certresolver: Traefik toont zijn zelfgetekende standaardcertificaat. De client kreeg TLS 1.3 met SNI `tls.prb237.test`.
- **Labels:** die van `web` uit `docker-compose.yml` (main), gerenderd met `docker compose config` en dummywaarden. Set 1 met `INSTALLATIE=prb237`, `DOMEIN=tls.prb237.test`: de routers zoals in productie op `websecure` met `tls=true`. Set 2 met `INSTALLATIE=prb237h`, `DOMEIN=http.prb237.test` en `compose.dev.yml` erbij: de routers op `web` zonder TLS. In set 2 is alleen `traefik.docker.network` op `prb237_voorkant` gezet. Beide sets hebben een eigen middleware `inlogrem` en dus een eigen teller (30 per minuut, burst 20).
- **Upstream:** per set een stub (`python:3.14-slim`) die het lichaam leest, 200 geeft met de kop `X-Stub: 1` en elk ontvangen pad logt. Zo meet de proef de eigen teller van deze Traefik. Flask en Gunicorn waren niet nodig, omdat geen gecodeerd pad de upstream bereikte.
- **Client:** een container op `prb237_klant`, die Traefik bereikt via de netwerkaliassen `tls.prb237.test` en `http.prb237.test`. Elke aanroep is `POST` met alleen de kop `Content-Length: 0`, zonder lichaam, en de `Host`-kop zelf gezet (`skip_host=True`).
- **Verloop per run:** 25 keer `POST /inloggen` als positieve controle. Daarna per variant eerst één `POST /inloggen` (bevestigt dat de teller boven de grens zit) en dan vijf keer de variant. Alles over één keep-alive-verbinding: in elke run bleef het bij één verbinding, en een run duurde 1,1 tot 1,3 seconde. De grens vult één plek per 2 seconden bij, dus de aanroepen kwamen sneller dan het bijvullen.
- **Herhaling:** drie rondes, met een herstart van Traefik tussen de rondes; per ronde eerst TLS en dan zonder TLS.

## Uitkomst

De positieve controle gaf in alle zes runs 20 keer 200 van de stub en vanaf de 21e aanroep 429. Elke tussentijdse `POST /inloggen` gaf 429 (20 van de 20 per run).

"Wie" volgt uit de kop `X-Stub` en de log van de stub. De log van de stub telde 120 regels, allemaal `POST /inloggen`: precies de 20 aanroepen onder de grens van elke run. De 400's staan niet in de toegangslog van Traefik; Traefik weigert ze vóór de routering.

| Pad (POST, boven de grens) | websecure, TLS (3 rondes) | web, zonder TLS (3 rondes) | Wie | Mutant zonder opties, TLS en zonder TLS |
|---|---|---|---|---|
| `/%2Finloggen` | 400 | 400 | Traefik | 200 van de stub |
| `/%2finloggen` | 400 | 400 | Traefik | 200 van de stub |
| `/inloggen%2F` | 400 | 400 | Traefik | 429 |
| `/%2Finloggen/code` | 400 | 400 | Traefik | 200 van de stub |
| `/.%2Finloggen` | 400 | 400 | Traefik | 200 van de stub |
| `/%5Cinloggen` | 400 | 400 | Traefik | 200 van de stub |
| `/inloggen%5C` | 400 | 400 | Traefik | 429 |
| `/%252Finloggen` | 400 | 400 | Traefik | 200 van de stub |
| `/inloggen%25` | 400 | 400 | Traefik | 429 |
| `/%00inloggen` | 400 | 400 | Traefik | 200 van de stub |
| `/inloggen%00` | 400 | 400 | Traefik | 429 |
| `/%2Fuitnodiging/abc` | 400 | 400 | Traefik | 200 van de stub |
| `/uitnodiging%2Fabc` | 400 | 400 | Traefik | 429 |
| `//inloggen` | 429 | 429 | Traefik | 429 |
| `/./inloggen` | 429 | 429 | Traefik | 429 |
| `/x/../inloggen` | 429 | 429 | Traefik | 429 |
| `/inloggen/` | 429 | 429 | Traefik | 429 |
| `/inloggen;x` | 429 | 429 | Traefik | 429 |
| `/inloggen?x=1` | 429 | 429 | Traefik | 429 |
| `/%69nloggen` | 429 | 429 | Traefik | 429 |

Elke cel staat voor vijf aanroepen met dezelfde status; in geen enkele run week een aanroep af. Traefik voegt `//`, `/./` en `/x/../` zelf samen en decodeert `%69`, dus die paden vallen onder de router `inloggen` en de rem. In de mutant omzeilt een gecodeerd teken vóór `inloggen` of `uitnodiging` de rem; een gecodeerd teken erna niet, omdat `PathPrefix` dan nog past.

## Conclusie

De opties voor gecodeerde tekens werken op `websecure` met TLS precies zoals op `web` zonder TLS. Met de entrypointopties uit het voorbeeld is de rate limit op inloggen niet te omzeilen met `%2F`, `%5C`, `%25` of `%00`. De vraag uit #237 en uit `werk/security/2026-11-10-probe-dast.md` (open vraag 1) is daarmee beantwoord.

Een gedeelde Traefik zonder deze opties blijft omzeilbaar op de proxylaag, met en zonder TLS (mutant). Daar beschermt alleen de applicatielaag, die volgens ADR-013 zelf 400 geeft op een gecodeerd pad. Dat is de bekende keuze uit ADR-013: de opties zijn aanbevolen, geen eis aan de gedeelde Traefik.

## Niet getoetst

- De applicatielaag (Werkzeug en de weigering van een gecodeerd pad in `web`); daar heeft de stub geen routes voor. Die laag is getoetst in de DAST van 2026-11-10 en in de proef van ADR-013.
- Een certificaat van Let's Encrypt of Pebble; de proef gebruikt het standaardcertificaat van Traefik. De opties werken op het entrypoint en hangen niet van het certificaat af.
- HTTP/2 en HTTP/3: de client sprak HTTP/1.1 over TLS 1.3. Een browser kiest met ALPN meestal HTTP/2.
- Een load balancer met PROXY protocol vóór Traefik (#54).
- De socketproxy uit het voorbeeld; Traefik las de Docker-socket direct (alleen lezen).
- `/uitnodiging` zonder pad erachter, en GET-aanroepen.

## Scripts en uitvoer

Scripts zonder geheimen in `/private/tmp/claude-502/-Users-reinoud-git-botenloods/28481ff3-6292-42ef-b2e5-8ac0ef6b49c0/scratchpad/probe-237/scripts/`:

- `maak_compose.py <map>`: maakt `compose.json` uit `render-tls.json` en `render-http.json` (gerenderd met `docker compose config`, zie hierboven);
- `draai.sh <map>`: start de stack en draait drie rondes met een herstart van Traefik ertussen; ruimt niet op;
- `mutant.sh <map>`: dezelfde proef zonder de opties voor gecodeerde tekens;
- `proef.py` (client) en `stub.py` (upstream).

Uitvoer per run, met tijdstempel, in `…/probe-237/uitvoer/` (zelfde map). Opruimen: `docker compose -f <map>/compose-mutant.json --profile klant down -v --remove-orphans`.

## Opruimen

Stack `prb237` afgebroken met `down -v --remove-orphans`. Daarna toonden `docker ps -a`, `docker network ls` en `docker volume ls` niets met `prb237`. De gedeelde stack `botenloods-*` en het netwerk van een andere agent (`agent-a6f58b18…`) zijn niet aangeraakt.
