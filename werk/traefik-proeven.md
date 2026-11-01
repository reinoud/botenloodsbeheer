# Proeven Traefik (ADR-013, issue #29)

**Datum:** 2026-10-31
**Uitgevoerd door:** forge
**Versie Traefik:** `traefik:v3.7.17` (`traefik version`: 3.7.17, linux/arm64)

## Opzet

- **Lokaal:** de stack uit `docker-compose.yml` met `compose.dev.yml`, met een eigen Traefik. Toegangslog van Traefik aan (`--accesslog=true`), zoals een gedeelde Traefik. De routers van `web` staan lokaal op het entrypoint `web` zonder TLS.
- **Productielabels:** een tweede stack in de scratchpad, project `botenloods-proef`, alleen `docker-compose.yml`, met `APP_OMGEVING=productie`, `INSTALLATIE=botenloods-proef`, `KOPPELNET=10.203.88.0/24`. De netwerken zijn aangemaakt zoals in `documentatie/beheer/installatie.md` (`docker network create --internal`). Een losse Traefik met entrypoints `web` (80, op 127.0.0.1:18080), `websecure` (443, op 127.0.0.1:18443) en `intern` (8081, niet gepubliceerd), een zelf ondertekend certificaat voor `localhost` als standaardcertificaat en `TRAEFIK_CERTRESOLVER=proef` (bestaat niet). Na de proeven opgeruimd.
- **Koppeling:** aanroepen vanaf `koppeling` met `docker run --rm --network botenloods_koppeling --entrypoint python botenloods-app <script>`.

Tokens en codes staan hieronder niet; ze kwamen uit `flask token robot` en `flask beheerder uitnodigen`.

## Uitkomst per controle

| Controle | Commando | Uitkomst | Oordeel |
|----------|----------|----------|---------|
| TLS 1.2 en hoger | `openssl s_client -connect 127.0.0.1:18443 -tls1_1 -cipher 'DEFAULT:@SECLEVEL=0'`; idem `-tls1_2 -CAfile cert.pem -verify_hostname localhost`; `-tls1_3` | 1.1: `tlsv1 alert protocol version` (alert 70). 1.2: `Protocol: TLSv1.2`, `verify return:1`, `subject=CN=localhost`. 1.3 slaagt | Geslaagd met een eigen certificaat. Een geldig certificaat via ACME kon lokaal niet |
| Certresolver | logs van de losse Traefik | `Router uses a nonexistent certificate resolver` per router; Traefik toont dan het standaardcertificaat | Gedrag bij een verkeerde naam vastgesteld; ACME zelf niet getest |
| Doorverwijzing van 80 | `curl -I 'http://localhost:18080/uitnodiging/x?zoek=y'` | `308 Permanent Redirect`, `Location: https://localhost/uitnodiging/x?zoek=y`; geen regel in de log van Traefik | Geslaagd |
| Headers | `curl -I` op `/`, op `/bestaat-niet` en op een 429 (`POST /inloggen`), lokaal en op 18443 | CSP, `nosniff`, `Referrer-Policy`, `Permissions-Policy` overal; HSTS `max-age=31536000` op https (op http niet, zoals bedoeld); geen `Server`-header | Geslaagd |
| Rate limit inloggen | 25 keer `curl -X POST http://localhost:8080/inloggen`; 25 keer GET; 22 keer `POST /uitnodiging/x/wachtwoord` | POST: 20 keer 400 (CSRF), daarna 5 keer 429 met `Retry-After: 1`. GET: 25 keer 200. Uitnodiging: 20 keer 400, dan 429 | Geslaagd |
| Rate limit per token | 12 aanroepen `GET /api/v1/ik` met token A in een seconde, dan token B | `[200 ×10, 429, 429]`, B: 200. 429 met `Retry-After: 1`, `nosniff`, tekst `Too Many Requests`, geen `Content-Type` | Geslaagd |
| Nep-geheim met dezelfde prefix (AEG-01) | E2E `test_nep_geheim_met_dezelfde_prefix_remt_het_echte_token_niet` | zie E2E-uitkomst in het antwoord van forge | Geslaagd als de E2E slaagt |
| Rate limit per IP | 60 aanroepen met willekeurige tokens vanaf `koppeling` | 50 keer 401, vanaf de 51e 429 | Geslaagd |
| Grens 2 MB als JSON | `PUT /api/v1/leden` met 2.218.901 bytes vanaf `koppeling` | 413, `application/json`, `{"fout":"Het verzoek is groter dan 2 MB."}`; één regel in de log van `api` | Geslaagd |
| Buitengrens 3 MB | `PUT` met `Content-Length` 3,5 MB (alleen de kop, `http.client`) | 413 `Request Entity Too Large` van Traefik. Met het hele lichaam sluit Traefik de verbinding (client: `Connection reset by peer`) | Geslaagd; de E2E stuurt daarom alleen de kop |
| 1 MB algemeen | 1,5 MB `POST` op `/leden` en `/inloggen` | 413 en 413 | Geslaagd |
| 10 MB op `/boten` | Playwright in de e2e-container, ingelogd: boot met een PNG van 9.190.018 bytes; daarna 11 MB `POST /boten/1/foto` | 9 MB: 302, "De boot is vastgelegd." 11 MB: 413 | Geslaagd. Zonder inlog geeft 9 MB 502, omdat de applicatie op CSRF weigert zonder het lichaam te lezen |
| Publieke kant kent `/api/` niet | `curl http://localhost:8080/api/v1/ik`; `https://localhost:18443/api/v1/ik` | `404 page not found` (Traefik), beide | Geslaagd |
| Entrypoint intern | E2E `test_ik_via_de_interne_server` (vanaf het adres van traefik op `koppeling`) en `test_intern_alleen_vanaf_koppeling` (vanaf 127.0.0.1); `curl http://localhost:8081` vanaf de host | 200; 404; geen verbinding (exit 7) | Geslaagd |
| `X-Forwarded-For` | vanaf `koppeling` (eigen adres 10.203.0.4) met een token dat alleen 10.203.0.99 toestaat: zonder kop, met `X-Forwarded-For: 10.203.0.99`, met `X_Forwarded_For: 10.203.0.99`, met `X-Real-Ip` en `Forwarded` | Vier keer 401; log van `api`: vier regels met `10.203.0.4`. Ook op 18443 met een vervalste kop: log van `web` toont het adres van de client | Geslaagd |
| Logformaat, één regel per verzoek | 50 aanroepen met willekeurige tokens; `/leden?zoek=Zoekterm<code>`, `/uitnodiging/<code>`, `POST /uitnodiging/<code>/wachtwoord`; daarna `docker compose logs \| grep` | 50 regels in `api`, 0 in Traefik. In `web`: `"GET /leden" 302`, `"GET /uitnodiging/..." 200`, `"POST /uitnodiging/..." 400`. Code en zoekterm staan in geen log, behalve één regel van Traefik voor `GET /api/v1/x?zoek=...` op de publieke kant (geen router, zie vraag 8) | Geslaagd, met de kanttekening bij vraag 8 |
| Health zonder rate limit | 100 keer `curl http://localhost:8080/health/live` | 100 keer 200 | Geslaagd |
| Ongezonde container | `docker compose stop web`, dan `start web` | Gestopt: 404. Tijdens `starting`: 404. Na `healthy`: 200. Met `--providers.docker.allowemptyservices=true`: gestopt 404, starting 500 | Traefik slaat ongezonde containers over. ADR-013 verwacht 503; dat geeft de Docker-provider niet |
| Toegangslog van Traefik uit per router (vraag 8) | alle proeven hierboven met `--accesslog=true` | Geen enkele regel voor verzoeken die een router van de botenloods raakten, ook niet voor 429, 413 en de doorverwijzing. Wel regels voor verzoeken zonder router: `HEAD /api/v1/ik` 404 op de publieke kant, een onbekende host, en `GET /api/v1/leden/importverzoek` toen `api` nog startte | Geslaagd |

## Bevindingen buiten de tabel

- Traefik waarschuwt bij het starten dat `aliasHeadersStrategy` niet is ingesteld: een kop als `X_Forwarded_For` gaat ongewijzigd door. De proef hierboven toont dat Gunicorn zo'n kop niet als `X-Forwarded-For` gebruikt. Aanbeveling voor de gedeelde Traefik: `aliasHeadersStrategy` op `delete` of `reject`. Die eis staat nog niet in ADR-013.
- Een verzoek op de publieke kant dat bij geen router past (alleen `/api/...` op `DOMEIN`, of een onbekende host), komt met querystring in de log van de gedeelde Traefik. De applicatie maakt zulke links niet.
- Tijdens het starten van `api` geeft Traefik 404. De integratiecontainer wacht daarom op een gezonde `api` (`depends_on`), anders volgt na de eerste mislukte ronde een uur pauze.
- De 429 van Traefik heeft geen `Content-Type`; de OpenAPI-specificatie noemt `text/plain`.

## Niet aangetoond

- Een geldig certificaat van een echte certresolver (ACME) voor `DOMEIN`: lokaal geen publieke DNS.
- Poort 443 en 80 op een echte host achter een gedeelde Traefik met socketproxy. Het voorbeeld `documentatie/beheer/voorbeelden/traefik/compose.yml` is met `docker compose config` en een korte start gecontroleerd, zie het antwoord van forge.
