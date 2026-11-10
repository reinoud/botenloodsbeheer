# DAST vóór release v1.0.0

**Datum:** 2026-11-10 en 2026-11-11
**Agent:** probe
**Commit:** 6ee8ee9 (main), in een eigen worktree, zonder de mounts van `app/`
**Image:** `botenloods-dast-app` sha256:15179f55b0, gebouwd uit de worktree en na afloop verwijderd
**Normen:** ADR-001, ADR-005, ADR-008, ADR-012, ADR-013, ADR-014; overlay §6 en §7

## Oordeel

De release is vanuit DAST niet geblokkeerd. Ik vond één nieuwe bevinding met ernst laag: een IPv6-adres met zone-index in de whitelist van een token geeft fout 500. De vier bevindingen van de vorige ronde (PRB-01 tot en met PRB-04) zijn opgelost. Tokenschermen, CSV-imports en -exports, de uploadgrenzen van 10 en 25 MB, het logo, de pagina Eigenaar onbekend en de regels voor clubboten gedragen zich volgens de ADR's.

## Scope en opzet

Eigen worktree van 6ee8ee9 en een eigen stack `botenloods-dast` (`INSTALLATIE=botenloods-dast`, `KOPPELNET=10.203.88.0/24`, Traefik op 127.0.0.1:18088 en :18443). Een extra compose-bestand in de scratchpad zette de mounts van `app/` en `--reload` uit, gaf de images een eigen naam en haalde de databasepoort weg. Eigen omgevingsbestand met nieuwe geheimen, lege database.

Leden kwamen via `PUT /api/v1/leden` uit `tests/fixtures/leden.json`, eerst zonder en daarna met opzegdatums (zoals `draai.sh` sinds #220), daarna `flask seed` als worker. Resultaat: 210 leden, 11 rekken, 229 plaatsen, 180 boten. De seed wijkt daarmee af van de omvang in de brief (10 rekken, 160 plaatsen); voor deze proeven maakt dat niet uit. Vier beheerders via `flask beheerder uitnodigen`, met wachtwoord en TOTP: drie voor de handmatige proeven en één voor ZAP. Drie robottokens via de CLI en enkele persoonlijke tokens via het scherm.

ZAP `stable` draaide in de netwerkruimte van Traefik, op drie manieren:

| Scan | Doel | Duur | Opmerking |
|------|------|------|-----------|
| Web, niet ingelogd | spider, passief, active | volledig | |
| Web, ingelogd | 23 startpaden, spider (992 URL's), passief, active | active afgekapt op 20 min | uitgesloten: uitloggen, intrekken, beheerders, instellingen, profiel, inloggen |
| API | OpenAPI-import, passief, active | active afgekapt op 15 min | token met alle leesrechten, 1,1 s pauze per verzoek |

De eerste anonieme scan startte niet, omdat poort 8080 in die netwerkruimte bezet is; de herhaling op een andere poort telt. Na de eerste minuut van de ingelogde scan gaf de toegangslog 200 op `/indeling`, `/wachtlijst` en `/leden`; tot het einde bleef dat zo.

Niet getest:

- passkeys (geen virtuele authenticator);
- TLS, HSTS en de vlag `Secure` op de sessiecookie (lokaal zonder TLS);
- de bron e-boekhouden zelf: de integratiecontainer praat met een externe dienst. Ik heb wel vijandige ledennamen via de API ingevoerd, zoals een bron die zou doen;
- DoS en grote aantallen gelijktijdige uploads (niet geautoriseerd);
- de schrijfroutes van de API met fuzzing: het token van de API-scan had geen recht `leden:importeren`, dus ZAP kreeg daar 403. De import heb ik met de hand getoetst.

## Bevindingen

| Code | Ernst | Route | Kort | Issue |
|------|-------|-------|------|-------|
| PRB-05 | laag | `POST /tokens/nieuw` | IPv6-adres met zone-index in de whitelist geeft fout 500 | #231 |

### PRB-05: whitelist met zone-index geeft fout 500

**Reproductie.**
1. Log in als beheerder en open binnen 10 minuten `/tokens/nieuw`.
2. Kies een persoonlijk token met een geldig recht en zet in de whitelist een link-local IPv6-adres met een zone-index (het teken `%` en een interfacenaam) en een prefixlengte.
3. Verstuur het formulier.

**Verwacht:** de melding over de whitelist op het formulier, zoals bij elke andere ongeldige reeks.
**Gevonden:** 500 met de standaardpagina. De log van `web` krijgt een ERROR-regel met traceback: `DataError`, PostgreSQL weigert de waarde als `cidr`. De controle in Python accepteert de reeks wel. Er komt geen token bij; de transactie wordt teruggedraaid.

**Gevolg:** geen lek. Alleen een ingelogde beheerder met een recente inlog kan het veroorzaken. Het lijkt op PRB-03: een kale foutpagina en een ERROR-regel in de log.

**Actie:** weiger een reeks met zone-index in `whitelist_lezen` met de bestaande melding. Regressieproef: dezelfde invoer geeft 200 met de melding en geen ERROR-regel.

## Hertoets vorige ronde

| Code | Proef | Uitkomst |
|------|-------|----------|
| PRB-01 | 21 keer `POST /inloggen`, daarna `/%2Finloggen`, `/%2finloggen`, `/inloggen%2F`, `/%5Cinloggen`, `/%00inloggen`, `/%252Finloggen` en de varianten op `/uitnodiging` | positieve controle 429 vanaf poging 22; alle gecodeerde varianten 400 van Traefik; `/inloggen/`, `/inloggen;x` en `?x=1` 429. Opgelost |
| PRB-02 | JPEG, PNG en WebP met EXIF (met GPS), ICC, COM-segment, tekstblok en XMP als foto | terug alleen APP0 en de beeldsegmenten, geen van de merktekens. Opgelost |
| PRB-03 | NUL-teken en te grote getallen in pad en querystring, zonder en met inlog, ook op de nieuwe routes | 400 of 404, geen 500 en geen ERROR-regel. Opgelost |
| PRB-04 | `DELETE /api/v1/plaatsen`, `POST /api/v1/boten`, onbekend pad | 405 en 404 als JSON. Opgelost. Een gecodeerd pad krijgt 400 van Traefik zonder lichaam, zoals de documentatie bij #133 beschrijft |

## Wat werkte

| Onderdeel | Proef | Uitkomst |
|-----------|-------|----------|
| Tokenschermen | positieve controle: persoonlijk token maken, waarde alleen in dat antwoord, `no-store`, token werkt op de API | geslaagd; overzicht toont geen waarde |
| Tokenrechten | `leden:importeren` geven via het scherm, bij maken en bij wijzigen; robottoken zonder whitelist; geldigheid 0, -5, 1096 en een te groot getal; naam met HTML; onbekende soort en recht | allemaal geweigerd met een melding; het CLI-recht blijft staan als een beheerder de rechten van het importtoken wijzigt |
| Recente inlog | sessie met een inlog van 11 minuten oud op tokens maken, wijzigen en intrekken, beide CSV-imports en bevestigen | 302 naar `/inloggen`; geen wijziging |
| Intrekken | beheerder C trekt het token van beheerder A in | de volgende API-aanroep 401 |
| CSRF | vals token op `/tokens/nieuw` | 400, geen token |
| Routes zonder sessie | 29 GET- en 13 POST-routes, ook de nieuwe | allemaal 302 naar `/inloggen` |
| CSV-import | groter dan 256 kB, meer dan 2000 regels, NUL-teken, latin-1, open aanhalingsteken, stuurteken, regeleinde in een veld, extensie `.txt` | 422 of een melding; niets geïmporteerd |
| CSV-koppelscherm | lid-id buiten de lijst, oud-lid, te groot getal, tekst, 3000 velden | "De keuzes kloppen niet meer"; bevestigen pas na een geldige keuze |
| Formules in exports | boten en ledennamen die met `=`, `+`, `-`, `@` of `'=` beginnen | in de CSV met een `'` ervoor; in `indeling.xlsx` als tekst (`inlineStr`, geen formule); een rondgang verandert niets |
| XSS | boot-, rek- en ledennamen met HTML via CSV, scherm en API | geëscaped op ruim twintig beheerpagina's, de kaartjes, het koppelscherm, de foutmeldingen van de import en de openbare pagina |
| Bedrijfsregels | lid-boot op een clubplaats, boot op een plaats zonder passende bootsoort, via beide toewijsroutes | geweigerd met een melding; positieve controle met een clubboot en een passende plaats geslaagd |
| Uploads foto en logo | SVG, HTML als PNG, GIF als JPEG, polyglot, PNG van 400 megapixel | geweigerd of opnieuw gecodeerd; logo als PNG met nosniff |
| Uploadgrenzen | 9,5 MB, 10,6 MB en 26 MB op `/boten`, `/boten/<id>/foto`, `/instellingen/logo`; 10,6 MB op de importroutes en `/inloggen` | 9,5 MB opgeslagen; 10,6 MB melding "groter dan 10 MB" en vorige blijft; 26 MB 413 van Traefik; 1 MB-routes 413 |
| Openbare pagina | 146 pagina's met een eigenaar op lidnummer en lidmaatschapsdatum | geen van beide; alleen code, boot, foto en naam |
| API-autorisatie | zonder token, vals token, token zonder recht, ingetrokken token, importtoken op een leesroute | 401 of 403; positieve controle 200; clubboot zichtbaar als `clubboot: true` zonder eigenaar |
| Ledenimport | namen met HTML, formule, 101 tekens, NUL, regeleinde, leeg | NUL en leeg tellen als ongeldig; de rest geëscaped of geneutraliseerd in de uitvoer |
| Rate limit inloggen | wisselende `X-Forwarded-For`, `X-Real-Ip` en `Forwarded` | 429 vanaf poging 21; de koppen tellen niet |
| Netwerk | vanaf het netwerk koppeling `db`, `api`, `web` en `worker` | niet op te lossen; alleen Traefik bereikbaar; `/api/v1/` op het entrypoint web 404 |
| Toegangslog | 16.081 regels in `web` | geen querystring, uitnodigingscode gemaskeerd, geen tokenwaarde of TOTP-code in een log, geen 5xx van ZAP |

## Triage scanneruitvoer

ZAP gaf in drie rapporten vier soorten meldingen. Geen ervan is een bevinding.

- *Private IP Disclosure* (laag, 5): `/log/techniek`, `/tokens` en `/tokens/nieuw` tonen whitelists en bronadressen. Dat is de bedoeling en staat achter inloggen. Valse positief.
- *User Controllable HTML Element Attribute* (informatief, 5): de velden van `/tokens/nieuw` komen terug in het formulier. Met `"><svg onload=…>` in elk veld bleef alles geëscaped. Valse positief.
- *Session Management Response Identified* en *User Agent Fuzzer* (informatief): beschrijvend, geen afwijking.

De sonde van ZAP op cloud-metadata (`/latest/meta-data/` en verwanten met een andere Host) kreeg 404 van Traefik; er is niets doorgestuurd.

## Observaties zonder actie

- Een niet-ingelogde client kan op `/boten…` en `/instellingen/logo…` tot 25 MB laten bufferen in het geheugen van Traefik; `web` leest het lichaam daarna weg en geeft 413. Dat volgt uit ADR-008 en ADR-013. Ik heb het niet onder belasting getoetst. Als foundation de buitengrens ooit herziet, is dit het punt om mee te wegen.
- Namen mogen bidi-tekens bevatten (zoals U+202E), ook in de ledenbron. Ze verschijnen omgekeerd op de openbare pagina. Alleen een beheerder of de bron kan ze invoeren.
- De integratiecontainer kan via Traefik de webinterface bereiken (`/inloggen`), net als elke bezoeker. De API alleen via het entrypoint intern.
- De dev-opbouw zet `db` op het netwerk `lokaal` met uitgang. In productie-opbouw niet.

## Open vragen

1. Niet blokkerend: geldt PRB-01 ook met TLS in productie-opbouw? De routers hebben dezelfde regels en de opties voor gecodeerde tekens staan op alle drie de entrypoints, maar ik heb het niet getest. Dezelfde vraag stond in de vorige ronde.

## Opruimen

ZAP-containers verwijderd. Stack `botenloods-dast` afgebroken met `down -v`; image `botenloods-dast-app` verwijderd; worktree verwijderd met `git worktree remove`. `docker ps -a`, `docker network ls`, `docker volume ls` en `docker images` tonen niets met `botenloods-dast`. Tokens, cookies, TOTP-geheimen en het omgevingsbestand in de scratchpad zijn gewist; de ZAP-rapporten bevatten geen sessie of token. Rapporten en scripts staan in de scratchpad onder `probe-securityronde-v1/`.
