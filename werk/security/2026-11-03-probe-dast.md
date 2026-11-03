# DAST na slice 11

**Datum:** 2026-11-03
**Agent:** probe
**Commit:** d2c34b7 (main) bij de start; code uit de werkmap via de mounts van `compose.dev.yml`
**Image:** `botenloods-app` sha256:6e26375e2a (Pillow 12.3.0) voor web, worker en de scans; api voor de proef met `compose.api-extern.yml` op sha256:b30e2dc110 (de nieuwe build voor #58)
**Normen:** ADR-001, ADR-005, ADR-008, ADR-009, ADR-013; overlay §7

## Oordeel

Eén bevinding met ernst middel: de rate limit op `/inloggen` en `/uitnodiging` is te omzeilen met een gecodeerde schuine streep in het pad. De vergrendeling per account blijft wel werken, dus wachtwoordraden blijft beperkt tot vijf pogingen per kwartier per account. Verder vond ik drie punten met ernst laag. Autorisatie, CSRF, sessies, tokens, whitelist, uploads en de openbare pagina gedragen zich volgens de ADR's.

## Scope en opzet

Eigen stack `botenloods-dast` (`INSTALLATIE=botenloods-dast`, `KOPPELNET=10.203.88.0/24`, Traefik op 127.0.0.1:18088 en :18443), met een eigen omgevingsbestand met nieuwe geheimen en een lege database. Leden kwamen via `PUT /api/v1/leden` uit `tests/fixtures/leden.json`, daarna `flask seed` als worker: 208 leden, 10 rekken, 160 plaatsen, 180 boten. Drie beheerders via `flask beheerder uitnodigen`, met wachtwoord en TOTP. Zeven robottokens met verschillende rechten en whitelists.

ZAP `stable` (automation framework) draaide op drie manieren:

| Scan | Doel | Duur | Opmerking |
|------|------|------|-----------|
| Web, niet ingelogd | spider, passief, active | volledig | |
| Web, ingelogd | 20 startpaden, spider (1734 URL's), passief, active | active afgekapt op 12 min | uitgesloten: uitloggen, intrekken, beheerders, instellingen |
| API | OpenAPI-import (9 URL's), passief, active | active afgekapt op 12 min | token met alle leesrechten, 1,1 s pauze per verzoek |

De eerste ingelogde webscan en API-scan stuurden geen sessie of token mee en tellen niet; de herhaling wel (bevestigd in de toegangslog). Niet getest: passkeys (geen virtuele authenticator gebruikt), de sessieduur van 12 uur, TLS en HSTS op de webrouters in productie-opbouw, en DoS buiten de grenzen.

Let op: de api-container herstartte drie keer tijdens de scans door `--reload`, omdat in de werkmap tegelijk aan #58 werd gewerkt. De stack draaide dus op de werkmap van dat moment.

## Bevindingen

| Code | Ernst | Route | Kort |
|------|-------|-------|------|
| PRB-01 | middel | `POST /inloggen`, `/inloggen/code`, `/uitnodiging/...` | Rate limit te omzeilen met `%2F` in het pad |
| PRB-02 | laag | `POST /boten/<id>/foto`, `/afbeelding/<sleutel>` | JPEG-commentaar blijft in de opgeslagen foto |
| PRB-03 | laag | `/p/<sleutel>`, `/afbeelding/<sleutel>`, `/boten/<id>` en andere | Fout 500 op een NUL-teken of een te groot getal, ook zonder inlog |
| PRB-04 | laag | `/api/v1/*` | API geeft bij 404 en 405 een HTML-pagina in plaats van JSON |

### PRB-01: rate limit op inloggen te omzeilen

**Reproductie.**
1. Stuur 21 keer kort na elkaar `POST /inloggen` met een geldig CSRF-token en een onbekende gebruiker. Vanaf poging 21 geeft Traefik 429.
2. Stuur direct daarna hetzelfde verzoek naar `POST /%2Finloggen`.
3. Herhaal stap 2 met de juiste gebruikersnaam en het juiste wachtwoord, en daarna `POST /%2Finloggen/code` met een juiste code.

**Verwacht:** 429 zolang de bucket leeg is (ADR-001, ADR-013: 30 per minuut, burst 20).
**Gevonden:** stap 2 geeft 302 naar `/inloggen` (de applicatie verwerkt de poging). Stap 3 geeft 302 naar `/inloggen/code` en daarna naar `/`; de sessie opent `/leden`. De varianten `//inloggen`, `/./inloggen` en `/static/../inloggen` krijgen wel 429; Traefik normaliseert die, maar laat `%2F` gecodeerd staan. Werkzeug decodeert `%2F` en voegt de dubbele schuine streep samen. De router `inloggen` matcht daardoor niet en het verzoek valt onder de router `web` zonder rem. De Traefik-log waarschuwt bij het starten voor gecodeerde tekens in het pad.

**Gevolg:** de rem per adres is weg. De vergrendeling per account (vijf pogingen, 15 minuten) blijft werken; dat heb ik met vijf foute TOTP-codes bevestigd. Een aanvaller kan zo wel onbeperkt argon2-berekeningen uitlokken.

**Actie:** laat Traefik een gecodeerde schuine streep in het pad weigeren op de entrypoints (de opties voor gecodeerde tekens waar de waarschuwing naar verwijst), of laat de router `inloggen` ook op de gecodeerde vorm matchen. Leg de keuze bij foundation (ADR-013). Regressieproef: na een lege bucket geeft `POST /%2Finloggen` 400 of 429, en nooit 302.

### PRB-02: JPEG-commentaar blijft staan

**Reproductie.** Upload als foto een JPEG met EXIF (met GPS), een ICC-profiel en een COM-segment met een herkenbare tekst. Haal het resultaat op via `/afbeelding/<sleutel>`.

**Verwacht:** geen EXIF, geen tekstblokken, geen ICC-profiel (ADR-008, overlay).
**Gevonden:** EXIF en ICC zijn weg. Het COM-segment staat er nog, met dezelfde tekst. Pillow schrijft `info["comment"]` bij het opslaan terug. De foto is openbaar.

**Actie:** sla de foto op zonder commentaar en voeg een bron met COM-segment toe aan de bestaande test op metadata. Hertest na #58, omdat die dezelfde code raakt.

### PRB-03: fout 500 op NUL-teken of te groot getal

**Reproductie.** Zonder inlog: `GET /p/%00` en `GET /afbeelding/%00`. Ingelogd: `GET /boten/99999999999999999999`, `/plaatsen/99999999999`, `/leden/2147483648` en `GET /leden?zoek=%00`.

**Verwacht:** 404 of 400.
**Gevonden:** 500 met de standaardpagina van Werkzeug, zonder stacktrace. Elke aanroep geeft een regel op niveau ERROR in de log van web. ZAP vond dezelfde klasse (3 keer 500 op `/boten/N`, `/plaatsen/N`, `/leden/N`).

**Gevolg:** geen lek. Wel kan iedereen zonder inlog ERROR-regels in de log zetten, wat echte fouten verbergt.

**Actie:** geef 404 bij een NUL-teken of een id buiten het bereik van `integer`, bijvoorbeeld met één controle vóór de query.

### PRB-04: HTML-foutpagina op de API

**Reproductie.** `DELETE /api/v1/plaatsen` en `GET /api/v1/bestaatniet` met een geldig token, via het koppelnet.

**Verwacht:** JSON zoals de andere fouten van de API.
**Gevonden:** 405 en 404 als HTML (`text/html`). Geen lek, wel lastig voor een koppeling die op JSON rekent.

**Actie:** errorhandlers voor 404 en 405 in de blueprint van de API, en de OpenAPI-beschrijving bijwerken.

## Wat werkte

| Onderdeel | Proef | Uitkomst |
|-----------|-------|----------|
| Security headers | elke webrespons | CSP zonder `unsafe-*`, `frame-ancestors 'none'`, nosniff, Referrer-Policy, Permissions-Policy, geen `Server` |
| Clickjacking | `frame-ancestors 'none'` op alle pagina's | geweerd |
| Cookie | `session` | `HttpOnly`, `SameSite=Lax`; `Secure` alleen bij `https://` in `BASIS_URL` (lokaal http, dus niet getoetst) |
| CSRF | positieve controle 302; zonder token, vals token en token van een andere sessie 400 | geen rek aangemaakt |
| Routes zonder sessie | 23 GET-routes | allemaal 302 naar `/inloggen` |
| Uitloggen | oude cookie hergebruikt | 302 naar `/inloggen` |
| Vergrendeling | 5 foute TOTP-codes, daarna juiste gegevens | geweigerd |
| Open redirect | geen `next`; `terug` alleen tegen een vaste waarde | geen |
| XSS | rek- en verenigingsnaam met HTML | geëscaped; CSP blokkeert inline script |
| CSS-injectie | kleur met `;}` | geweigerd |
| Openbare pagina | alle 160 `/p/`-pagina's op e-mail, telefoon, adres en postcode | alleen code, boot, naam, logo |
| Uploads | SVG, HTML als `.jpg`, GIF, polyglot, PNG van 81 megapixel | geweigerd of opnieuw gecodeerd; nosniff |
| Grootte | 10 MB op `/boten`, 1 MB elders | 413 boven de grens |
| API-autorisatie | zonder token, vals token, token zonder recht, ingetrokken token, whitelist buiten bereik | 401 of 403; positieve controle 200 |
| Persoonsgegevens | `leden:lezen` zonder en met `persoonsgegevens` | adres, telefoon en e-mail alleen met het recht |
| Rate limit API | 25 aanroepen per token; 70 met verschillende nepkoppen | 429 na 11 en na 51; varianten van de kop geven 401 |
| Import | geen JSON, verkeerd type, lege lijst, meer dan 2 MB | 422, 409 (veiligheidsgrens), 413 in JSON |
| API van buiten | `config` zonder `API_EXTERN_BRONNEN`; met bron 172.25.0.1/32 | weigert te starten; toegestane bron 200, andere bron 403, token met whitelist koppelnet 401, vervalste `X-Forwarded-For` 401, `api%2Fv1` 404 |
| Toegangslog | eigen markeringen | één regel per verzoek in web, geen querystring, uitnodigingscode gemaskeerd, niets in de log van Traefik, geen tokens in de log van api, echt clientadres bij vervalste `X-Forwarded-For` |

## Triage scanneruitvoer

ZAP gaf in zes rapporten twee soorten meldingen. Geen ervan is een bevinding.

- *Private IP Disclosure* (laag, 3): `/log/techniek` en `/tokens` tonen bronadressen en whitelists. Dat is de bedoeling en staat achter inloggen. Valse positief.
- *Session Management Response Identified* en *User Agent Fuzzer* (informatief): beschrijvend, geen afwijking.

## Observaties zonder actie

- De paden `/p/<sleutel>` en `/afbeelding/<sleutel>` staan voluit in de toegangslog. De sleutels staan ook op het openbare kaartje en zijn geen persoonsgegevens.
- Gunicorn logt bij een te lange verzoekregel het adres van Traefik in plaats van de client.

## Open vragen

1. Niet blokkerend: geldt PRB-01 ook in productie-opbouw met TLS? Ik verwacht van wel, omdat de routers dezelfde regels hebben, maar dat heb ik niet getest.

## Opruimen

Stack `botenloods-dast` afgebroken met `down -v`; geen containers, netwerken of volumes over. Geen images gebouwd. Opgehaald en blijven staan: `ghcr.io/zaproxy/zaproxy:stable`. Opgehaald en verwijderd: `curlimages/curl:8.11.1`. Tokens, cookies, TOTP-geheimen en het omgevingsbestand in de scratchpad zijn gewist. ZAP-rapporten en logs staan in de scratchpad onder `probe-securityronde/`.
