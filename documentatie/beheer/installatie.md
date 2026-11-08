# Installatie achter een gedeelde Traefik

Deze handleiding is voor de systeembeheerder van een vereniging. Eén installatie dient één vereniging. De applicatie draait in docker-compose achter een Traefik die op dezelfde host ook andere diensten bedient. Die Traefik draait in een eigen compose-stack; de compose van de botenloods levert alleen labels (ADR-013).

Andere delen: [voorbeelden](voorbeelden.md) (images binnenhalen of zelf bouwen), [integratiecontainer](integratiecontainer.md) (leden importeren), [API van buiten](api-van-buiten.md) en [bijwerken, tokens en logs](bijwerken.md).

## Opbouw

| Dienst | Taak | Netwerken |
|--------|------|-----------|
| `web` | webinterface voor de beheerders en de openbare pagina | `achterkant`, `voorkant` |
| `api` | `/api/v1`, standaard alleen voor de integratiecontainer; van buiten alleen met `compose.api-extern.yml` ([API van buiten](api-van-buiten.md)) | `achterkant`, `voorkant` |
| `worker` | achtergrondtaken, zoals de opschoning | `achterkant` |
| `migrate` | databasemigraties bij het starten | `achterkant` |
| `db` | PostgreSQL 17 | `achterkant` |
| `integratie` | haalt de leden uit de ledenbron | `koppeling`, `buiten` |

`achterkant` en `buiten` maakt compose zelf. `voorkant` en `koppeling` maakt de beheerder vooraf, zodat de gedeelde Traefik ze kan opnemen. `web` en `api` staan nooit op het netwerk van Traefik met andere diensten: daar zou elke dienst `api` rechtstreeks kunnen aanroepen.

## Eisen aan de gedeelde Traefik

De labels zijn getest met `traefik:v3.7.17`. Een andere versie vraagt dat de proeven uit ADR-013 opnieuw slagen. Een voorbeeld van zo'n stack staat in `voorbeelden/traefik/compose.yml`. De Traefik moet:

- de Docker-provider gebruiken met `exposedByDefault=false`;
- de entrypoints `web` (80), `websecure` (443) en `intern` (8081) hebben, met precies die namen;
- `intern` niet publiceren naar de host;
- op geen van de drie `forwardedHeaders.trustedIPs` of `forwardedHeaders.insecure` zetten, zodat hij een binnenkomende `X-Forwarded-For` niet vertrouwt;
- op alle drie `http.aliasHeadersStrategy=delete` zetten (`--entrypoints.<naam>.http.aliasheadersstrategy=delete`), zodat een kop als `X_Forwarded_For` niet ongewijzigd doorgaat;
- aangesloten zijn op `<INSTALLATIE>_voorkant` en `<INSTALLATIE>_koppeling`;
- een certresolver hebben die het certificaat van `DOMEIN` bij Let's Encrypt aanvraagt. In het voorbeeld heet die `letsencrypt` en gebruikt hij de TLS-challenge, dus poort 443 moet vanaf internet bereikbaar zijn en `DOMEIN` moet naar de host wijzen.

Aanbevolen, geen eis: zet op de drie entrypoints `http.encodedCharacters.allowEncodedSlash`, `allowEncodedBackSlash`, `allowEncodedNullCharacter` en `allowEncodedPercent` op `false` (`--entrypoints.<naam>.http.encodedcharacters.<optie>=false`, zoals in het voorbeeld). Traefik weigert dan een pad als `/%2Finloggen` zelf met 400. De botenloods weigert zo'n pad ook zelf met 400, dus zonder de opties is de rate limit op inloggen niet te omzeilen. De opties raken wel andere diensten op dezelfde entrypoints, controleer eerst dat die geen gecodeerde schuine strepen nodig hebben.

De toegangslog van Traefik mag aan staan: elke router van de botenloods zet hem voor zichzelf uit. Een verzoek dat bij geen enkele router past, zoals `https://DOMEIN/api/...`, schrijft Traefik wel in zijn log. Dat geldt ook zolang `web` start of gestopt is: dan heeft `web` geen router, en komen alle paden, ook codes en zoektermen, in de log van de gedeelde Traefik.

Traefik leest de Docker-socket. Wie die socket leest, heeft de rechten van root op de host. Laat Traefik daarom via een socketproxy lezen die alleen leesrechten op containers geeft, zoals in het voorbeeld. Ook met alleen leesrechten zijn via `inspect` alle omgevingsvariabelen van de containers leesbaar, dus ook de geheimen in `.env`. Geef de socketproxy daarom alleen aan Traefik.

Staat er een load balancer vóór Traefik, laat die dan het clientadres doorgeven met het PROXY protocol. Vertrouw dat in Traefik alleen van de load balancer: `--entrypoints.websecure.proxyprotocol.trustedips=<adressen van de load balancer>`, en op `web` als die ook poort 80 doorstuurt (zie het voorbeeld). Zet de optie alleen als de load balancer op elke verbinding zelf een PROXY-kop zet (zoals `send-proxy`), en alleen met de exacte adressen van de load balancer (`/32` of `/128`), nooit met een subnet waarin ook andere machines staan. Anders kan een client zelf een PROXY-kop sturen en elk adres opgeven; dan omzeilt hij `externtoegang`, `iprem` en de rem op inloggen. Zet de optie niet op `intern` en zet nergens `proxyProtocol.insecure`. `PROXY_HOPS` blijft 1 en de middlewares krijgen geen `ipStrategy`. Een load balancer met alleen `X-Forwarded-For` wordt niet ondersteund ([API van buiten](api-van-buiten.md)).

## Stap 1: netwerken aanmaken

Kies een naam voor de installatie (`INSTALLATIE`, standaard `botenloods`) en een vrij subnet voor `koppeling` (`KOPPELNET`, standaard `10.203.0.0/24`). Beide netwerken zijn intern:

```sh
docker network create --internal botenloods_voorkant
docker network create --internal --subnet 10.203.0.0/24 botenloods_koppeling
```

Het subnet moet gelijk zijn aan `KOPPELNET`. De router op `intern` laat alleen adressen uit dat subnet door. Neem beide netwerken op in de compose van Traefik en start die opnieuw.

## Stap 2: instellingen

Haal de bestanden op volgens een van de [voorbeelden](voorbeelden.md). Maak dan de instellingen en het bestand voor het token:

```sh
cp .env.example .env && chmod 600 .env
mkdir -p secrets && install -m 600 /dev/null secrets/api_token
```

Wachtwoorden en sleutels bevatten alleen letters en cijfers, want ze komen in een database-URL (`openssl rand -hex 32`). `.env.example` legt elke variabele uit.

| Variabele | Wat |
|-----------|-----|
| `APP_OMGEVING` | `productie`; alleen lokaal `ontwikkeling` |
| `BASIS_URL` | `https://` en de domeinnaam; QR-codes hangen eraan |
| `DOMEIN` | de host uit `BASIS_URL`, voor de routers |
| `INSTALLATIE` | naam voor netwerken en routers, uniek op de host |
| `TRAEFIK_CERTRESOLVER` | naam van de certresolver voor Let's Encrypt in Traefik, zoals `letsencrypt`; verplicht in productie |
| `WEBAUTHN_RP_ID` | leeg: de host uit `BASIS_URL`; passkeys hangen eraan |
| `SECRET_KEY` | ondertekent sessiecookies, minstens 32 tekens |
| `TOTP_SLEUTEL` | Fernet-sleutel voor de TOTP-geheimen |
| `POSTGRES_PASSWORD` | eigenaar van de database, alleen voor migraties |
| `DB_WEB_WACHTWOORD`, `DB_TAKEN_WACHTWOORD`, `DB_API_WACHTWOORD` | databaserollen van `web`, `worker` en `api` |
| `API_INGESCHAKELD` | `true` of `false`; uit weigert elke aanroep; `web` toont de stand op de statuspagina |
| `KOPPELNET` | subnet van `koppeling`, ook de standaardwhitelist van een robottoken |
| `LEDENBRON`, `LEDENBRON_STUB_BESTAND`, `SYNC_TIJDSTIP`, `API_URL`, `EBOEKHOUDEN_USERNAME`, `EBOEKHOUDEN_CODE1`, `EBOEKHOUDEN_CODE2`, `BOOTAANTALLEN_SCHRIJVEN` | integratiecontainer, zie [integratiecontainer](integratiecontainer.md) |
| `PROXY_HOPS` | aantal vertrouwde proxy's, achter Traefik 1 |
| `OPSCHOON_TIJDSTIP` | dagelijkse opschoning na 5 jaar in `worker`, standaard `04:00`, in de tijdzone `TZ` |
| `TZ`, `LOG_NIVEAU` | tijdzone en logniveau |

Een verkeerde of ontbrekende waarde stopt het starten van `web`, met de naam van de variabele in `docker compose logs web`.

## Stap 3: starten en de eerste beheerder

```sh
docker compose up -d
docker compose ps
```

Traefik stuurt pas verkeer naar `web` en `api` als hun healthcheck slaagt. Tot dan geeft het domein 404.

De eerste beheerder komt van de commandoregel. Volgende beheerders nodigt een beheerder uit via `/beheerders`:

```sh
docker compose exec web flask beheerder uitnodigen <gebruikersnaam>
```

De link werkt één keer en is 24 uur geldig. Open hem op de host uit `BASIS_URL` en kies een passkey of een wachtwoord met een authenticator-app.

Daarna volgt het token van de integratiecontainer, zie [integratiecontainer](integratiecontainer.md). Zonder token importeert hij geen leden.

## Probleem: wachtwoord van een databaserol geweigerd

In de log van `db` staat bijvoorbeeld:

```text
FATAL:  password authentication failed for user "botenloods_taken"
```

De rol bestaat, maar het wachtwoord in de database is niet het wachtwoord in `.env`. Dat gebeurt zo: `docker/db-init.sh` maakt de rollen `botenloods_web`, `botenloods_taken` en `botenloods_api` en zet hun wachtwoorden alleen bij de eerste start met een lege database. Bestaat het volume `dbdata` al, dan slaat PostgreSQL het script over. Een nieuwe `.env`, een gewijzigd wachtwoord of een volume van een eerdere installatie geeft dan deze fout. De rol in de melding hoort bij één dienst: `botenloods_taken` bij `worker`, `botenloods_web` bij `web` en `botenloods_api` bij `api`.

Staat er ook `DETAIL:  User "botenloods_taken" has no password assigned.`, dan heeft het script nooit gedraaid op deze database: de migratie heeft de rol zonder wachtwoord aangemaakt. Meestal stond `docker/db-init.sh` niet op de host bij de eerste start. Tot en met v0.2.0 maakte Docker dan een lege map op die plek, en PostgreSQL sloeg die over; latere versies weigeren te starten zonder het bestand. Controleer dat het een bestand is:

```sh
docker compose exec db ls -l /docker-entrypoint-initdb.d/
```

Staat er `rollen.sh` als map (een regel die met `d` begint), stop dan de stack, verwijder de map `docker/db-init.sh` op de host, haal het bestand op volgens de [voorbeelden](voorbeelden.md) en start opnieuw.

Zet daarna de wachtwoorden uit `.env` in de database:

```sh
docker compose up -d db
docker compose exec db sh /docker-entrypoint-initdb.d/rollen.sh
docker compose restart worker web api
```

De eerste regel maakt `db` opnieuw aan als `.env` is gewijzigd. Dat is nodig, want het script leest de wachtwoorden uit de omgeving van de container en die staat vast vanaf het moment dat de container is gemaakt. De gegevens in het volume blijven bewaard.

Blijft de fout, controleer dan of het wachtwoord alleen letters en cijfers bevat (zie stap 2). Een teken als `@`, `/`, `:` of `%` breekt de database-URL, en dan komt er een ander wachtwoord bij de database aan dan in `.env` staat.

## Controle

- `curl -I http://DOMEIN/` geeft 308 naar `https://`.
- `curl -I https://DOMEIN/inloggen` geeft 200 met `Strict-Transport-Security` en `Content-Security-Policy`, zonder `Server`.
- `https://DOMEIN/api/v1/ik` geeft 404, zolang `compose.api-extern.yml` er niet bij staat.
- `docker compose logs integratie` meldt na het token binnen een minuut `Import geslaagd`.
