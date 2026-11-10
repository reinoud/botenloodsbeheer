# botenloodsbeheer

Beheer van de botenloods van een kanovereniging. Projectregels: `docs/PROJECT-OVERLAY.md`. Architectuur: `docs/architecture/architectuur.md`.

## Documentatie

- Voor beheerders van de botenloods: [handleiding](documentatie/gebruikers/handleiding.md).
- Voor systeembeheerders (installatie achter Traefik, voorbeelden, integratiecontainer, bijwerken): [beheerdocumentatie](documentatie/beheer/installatie.md).

## Lokaal starten

1. `cp .env.example .env`, `chmod 600 .env` en de geheimen invullen (uitleg staat in het bestand). De standaarden `DOMEIN=localhost` en een lege `TRAEFIK_CERTRESOLVER` passen bij lokaal.
2. `mkdir -p secrets && install -m 600 /dev/null secrets/api_token`: zonder dat bestand start compose niet.
3. `docker compose -f docker-compose.yml -f compose.dev.yml up --build -d`. Lokaal start een eigen Traefik mee; de netwerken maakt compose zelf.
4. Een token voor de integratiecontainer maken en in `secrets/api_token` zetten volgens `documentatie/beheer/integratiecontainer.md`. Binnen een minuut importeert de container de synthetische leden met de stub. De import slaat een nieuw lid met een opzegdatum over (#203); wil je ook oud-leden, importeer dan eerst één keer zonder opzegdatums en laat daarna de container importeren. `tests/e2e/draai.sh` doet dat op een stack zonder leden zelf: `tests/e2e/eerste_import.py` in de container `e2e`, met een robottoken met `leden:importeren` en de whitelist op het adres van Traefik op het netwerk `koppeling`.
5. `docker compose -f docker-compose.yml -f compose.dev.yml exec worker flask seed` voor een synthetische loods (alleen buiten productie). Seed maakt geen leden: alleen de import via de API schrijft leden.
6. Een login aanmaken, zie hieronder.

De applicatie draait op http://localhost:8080. De API (`/api/v1`) is alleen bereikbaar via het entrypoint `intern` van Traefik op poort 8081, vanaf het netwerk `koppeling` (ADR-012, ADR-013).

### Een login aanmaken

De eerste beheerder maak je op de commandoregel. Elke volgende beheerder kan ook via `/beheerders` in de applicatie.

1. `docker compose -f docker-compose.yml -f compose.dev.yml exec web flask beheerder uitnodigen <gebruikersnaam>`. De gebruikersnaam is 2 tot 50 tekens: a-z, cijfers, punt, streepje en onderstreping.
2. Het commando toont een link (`<BASIS_URL>/uitnodiging/<code>`). Die werkt één keer en is 24 uur geldig.
3. Open de link en kies een passkey, of een wachtwoord van 12 tot 128 tekens met een authenticator-app (QR-code scannen en een eerste code invullen).
4. Log in op http://localhost:8080/inloggen.

Een passkey hangt aan de host uit `BASIS_URL` (of `WEBAUTHN_RP_ID`). Open de link dus op dezelfde host, `localhost` en niet `127.0.0.1`. Is de link verlopen of gebruikt, draai het commando dan opnieuw met een andere gebruikersnaam, of herstel de beheerder via `/beheerders`.

## API-token

- Maken: `docker compose exec web flask token robot <naam> --recht leden:importeren --recht bootaantallen:lezen`. Het token verschijnt één keer. Zonder `--whitelist` geldt `KOPPELNET`, zonder `--dagen` 365 dagen (hooguit 1095).
- Intrekken: `docker compose exec web flask token intrekken <naam>`. Vervangen is een nieuw token maken en het oude intrekken.
- Controleren: `GET http://traefik:8081/api/v1/ik` met `Authorization: Bearer <token>`, vanaf het netwerk `koppeling`. Het contract staat in `app/api/openapi.yaml`.
- Uitzetten: `API_INGESCHAKELD=false` in `.env` en `docker compose up -d api`.

## Bijwerken

Een update met een nieuwe databaserol (zoals `botenloods_api` in slice 5): zet het wachtwoord in `.env` (`DB_API_WACHTWOORD`) en draai vóór `up` eerst `docker compose up -d db` en `docker compose exec db sh /docker-entrypoint-initdb.d/rollen.sh`. Traefik volgt de containers zelf; een herstart van de proxy is niet nodig.

## Tests

- Unit en integratie: `docker compose -f docker-compose.yml -f compose.dev.yml run --rm test`
- E2E (stack moet draaien): `tests/e2e/draai.sh`, één test met `tests/e2e/draai.sh -k <naam>`. De hele suite draait per bestand, met 40 seconden pauze voor de rate limit op inloggen.

## Productie

Zie [installatie achter een gedeelde Traefik](documentatie/beheer/installatie.md). Het logo van de vereniging upload je als beheerder op Instellingen (JPEG, PNG of WebP); zonder logo toont de kopbalk alleen de naam.
