# Statische securityronde na slice 11

**Datum:** 2026-11-03
**Agent:** aegis
**Commit:** d2c34b7 (main)
**Normen:** ADR-001, ADR-005, ADR-008, ADR-009, ADR-012, ADR-013; overlay §7

## Oordeel

Niet goed genoeg, één punt blokkeert. Pillow 12.3.0 heeft bekende lekken, waaronder een heap-overflow in de JPEG-decoder. Die decoder verwerkt elke foto-upload. De oplossing is een update van het lockbestand. Voor de rest vond ik in de beoordeelde scope geen materiële bevinding in de code: autorisatie, CSRF, sessies, tokens, uploads en de import van leden volgen de ADR's.

## Scope

Beoordeeld: `app/`, `integratie/`, `migrations/`, `docker/`, de compose-bestanden en `.github/workflows/images.yml`. Verder `uv.lock` en `tests/e2e/requirements.txt` met pip-audit en trivy, de images `botenloods-app:latest` en `botenloods-integratie:latest` met trivy 0.67.2, en de tabelrechten met een leesquery in de gedeelde database.

Niet beoordeeld: templates per regel (wel gezocht naar `|safe` en onveilige JavaScript), de testcode, de documentatie en screenshots. Ook niet de DAST (dat doet probe). Ik heb geen proeven gedaan tegen de draaiende stack.

## Bevindingen

| Code | Ernst | Bestand:regel | Kort | Issue |
|------|-------|---------------|------|-------|
| AEG-01 | hoog | `uv.lock` (pillow 12.3.0), `app/domein/afbeeldingen.py:25` | Pillow met bekende lekken in de decoders | ja |
| AEG-02 | middel | `.github/workflows/images.yml` | Geen scan van afhankelijkheden of images in CI | ja |
| AEG-03 | laag | `uv.lock` (pyasn1 0.6.4), `tests/e2e/requirements.txt` (pytest 8.4.2) | Overige bekende lekken in afhankelijkheden | ja, samen met AEG-01 |
| AEG-04 | laag | `migrations/versions/0001_slice_1a_beheerders_log_en_techniek.py:106`, `0002_slice_1b_indeling_leden_boten.py:99` | Rol `botenloods_taken` heeft meer rechten dan de worker nodig heeft | ja |
| AEG-05 | laag | `.github/workflows/images.yml:28-42` | Actions op een versietag, met `packages: write` | ja |
| AEG-06 | laag | `docker-compose.yml:7-15` | web, api, worker en migrate missen `cap_drop: [ALL]` | ja |
| AEG-07 | laag | `app/domein/tokens.py:176`, `app/domein/opschonen.py:34` | Elke geweigerde API-aanroep wordt een logregel met IP-adres, 5 jaar bewaard | nee, adviespunt |

### AEG-01: Pillow met bekende lekken in de decoders

pip-audit en trivy melden 39 kwetsbaarheden in Pillow 12.3.0. Ze zijn allemaal opgelost in 13.0.0. Vijf hebben de ernst critical, waaronder een heap-overflow in `ImagingJpegDecode` (CVE-2026-112403). JPEG is een van de drie toegestane formaten, dus elke foto-upload loopt door die decoder. Daarnaast opent `Image.open` in `afbeeldingen.verwerk` het bestand met alle 43 geregistreerde formaten. De controle op JPEG, PNG en WebP volgt pas daarna, zodat ook de kopparsers van formaten als TIFF en FPX de invoer zien. De Ghostscript-CVE is niet bereikbaar: het image bevat geen `gs`.

Alleen een ingelogde beheerder kan uploaden, en CSRF is afgedekt. Toch kan een overgenomen sessie of een kwaadaardig bestand dat een beheerder argeloos uploadt, geheugen corrumperen in `web`. De rol `botenloods_web` heeft vanuit die container ruime schrijfrechten.

**Actie.** `uv lock --upgrade-package pillow` naar 13.0.0 (pyproject staat dat toe), het image opnieuw bouwen en de uploadtests draaien. Beperk daarnaast `Image.open(io.BytesIO(inhoud), formats=["JPEG", "PNG", "WEBP"])`. Dat is één argument, en een test met een TIFF-bestand moet daarna dezelfde Regelfout geven.

### AEG-02: geen scan van afhankelijkheden of images in CI

De workflow bouwt en pusht images bij een release zonder scan. Er is ook geen Dependabot of Renovate. AEG-01 is daardoor pas bij deze mijlpaalronde zichtbaar geworden. De handmatige ronde per mijlpaal (overlay §7) blijft gelden, maar een release kan tussen twee rondes vallen.

**Actie.** Voeg vóór de push een trivy-stap toe die faalt op een critical of high met beschikbare oplossing (`--ignore-unfixed`). Zet Dependabot aan voor `uv` en `github-actions`. Dat zijn twee kleine bestanden en geen nieuwe laag.

### AEG-03: overige bekende lekken in afhankelijkheden

- pyasn1 0.6.4 (via webauthn): vier CVE's voor denial of service, opgelost in 0.6.5. Bereikbaar bij het registreren van een passkey, dus alleen met een uitnodigingscode of een recente inlog.
- pytest 8.4.2 in `tests/e2e/requirements.txt`: PYSEC-2026-1845, opgelost in 9.0.3. Alleen testgereedschap.
- In beide images meldt trivy urllib3, msgpack en setuptools in de meegeleverde `pip` van het basisimage. pip draait niet tijdens gebruik.
- `psycopg_binary.libs` bevat pcre2 10.32 (trivy: critical, CVE-2022-1586). 3.3.7 is beschikbaar naast de huidige 3.3.6. Controleer na de upgrade of de melding verdwijnt.
- De Debian-pakketten (debian 13.7) hebben 45 tot 50 meldingen met ernst high. Geen daarvan heeft een oplossing in Debian; opnieuw bouwen na een nieuwe puntrelease is genoeg.

**Actie.** Neem pyasn1 en psycopg-binary mee in de lockupdate van AEG-01. Hoog pytest op in de e2e-requirements.

### AEG-04: rol botenloods_taken heeft te veel rechten

De migraties geven `botenloods_taken` dezelfde DML als `botenloods_web` op `beheerder`, `passkey`, `uitnodiging`, `instelling`, `rek`, `plaats`, `plaats_bootsoort` en `bootsoort`. Dat heb ik met een leesquery in de database bevestigd. De worker schrijft alleen `taakrun` en schoont `logregel`, `lid`, `boot`, `afbeelding` en `wachtlijst` op. Met de huidige rechten kan code in de worker een beheerder met uitnodiging aanmaken. De worker heeft geen inkomend verkeer, daarom is de ernst laag.

**Actie.** Een migratie met `REVOKE INSERT, UPDATE, DELETE` op de tabellen die de worker niet gebruikt. Zoek eerst welke tests en seedcode als `botenloods_taken` schrijven (briefingchecklist).

### AEG-05: actions op een versietag, met packages: write

`actions/checkout@v4` en de vier `docker/*`-actions staan op een versietag. Een gekaapte tag kan met `packages: write` een image pushen naar ghcr.io, en dat image draaien de verenigingen.

**Actie.** Zet elke action vast op een commit-SHA, met de versie als commentaar. Dependabot (AEG-02) houdt die bij.

### AEG-06: geen cap_drop op de app-diensten

`integratie` heeft `cap_drop: [ALL]`, het anker `x-app` niet. Gunicorn luistert op poort 8000 als gebruiker 10001 en heeft geen capabilities nodig.

**Actie.** `cap_drop: [ALL]` in `x-app`. Daarna controleren of web, api, worker en migrate healthy worden.

### AEG-07: geweigerde API-aanroepen in het log

Elke weigering, ook zonder token, schrijft een logregel met het IP-adres (ADR-005). De iprem-limiet staat 300 aanroepen per minuut per adres toe. Intern bereikt alleen de integratiecontainer de API, en met `compose.api-extern.yml` alleen de adressen uit `API_EXTERN_BRONNEN`. Met de API van buiten zijn het externe IP-adressen, en die blijven 5 jaar staan. Bij deze omvang is dat acceptabel. Ik stel geen issue voor, wel een zin in ADR-005 of het verwerkingsregister over de bewaartermijn van IP-adressen.

## Bekende issues

- **#25** geldt volgens de acceptatiecriteria voor elke `FROM`. Daar vallen ook `docker/Dockerfile:1` (`python:3.14-slim`) en het uv-image (`docker/Dockerfile:12`) onder, en in de compose `postgres:17`. Ernst blijft laag. Voeg dat als commentaar toe aan het issue.
- **#12** (geen recente inlog bij blokkeren, deblokkeren en verwijderen): ongewijzigd laag.
- **#20** geldt na de overstap op Traefik nog: `ProxyFix` vertrouwt `X-Forwarded-For` van elke afzender. web en worker kunnen `api:8000` direct bereiken over `achterkant` en `voorkant`. Ernst ongewijzigd.
- De andere genoemde issues heb ik niet hoger ingeschat.

## Wat klopt

Kort, als tegenbewijs:

- Elke route zonder `inloggen_vereist` is bewust openbaar: inloggen, uitnodiging, `/p/`, `/afbeelding/`, logo, huisstijl en health.
- De drempels zijn gelijk aan ADR-001: 5 pogingen en 15 minuten vergrendeling, sessie 12 uur, recente inlog 10 minuten, Traefik 30 per minuut met burst 20.
- Tokens volgen ADR-005: 256 bits, SHA-256 met `compare_digest`, een vaste volgorde van controles en één weigeringstekst. Het CLI-recht `leden:importeren` is via de web niet te geven of af te nemen.
- `leden.importeer` valideert type en lengte per veld en logt geen inhoud. De Excel-export voorkomt formules.
- Trivy vond geen geheimen in de images. `.env` en `secrets/` staan niet in git en hebben mode 0600.
- De CSP is streng, en er is alleen `|safe` op de door segno gemaakte SVG.

## Open vragen

1. Niet blokkerend: mag het integratie-image `pip` kwijt (`pip uninstall -y pip` na de build)? Dat haalt de meldingen van de meegeleverde pakketten weg. De container gebruikt alleen de standaardbibliotheek.
