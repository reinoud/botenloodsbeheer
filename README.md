# botenloodsbeheer

Beheer van de botenloods van een kanovereniging. Projectregels: `docs/PROJECT-OVERLAY.md`. Architectuur: `docs/architecture/architectuur.md`.

## Lokaal starten

1. `cp .env.example .env`, `chmod 600 .env` en de geheimen invullen (uitleg staat in het bestand).
2. `mkdir -p secrets && install -m 600 /dev/null secrets/api_token`: zonder dat bestand start compose niet.
3. `docker compose -f docker-compose.yml -f compose.dev.yml up --build -d`
4. Een token voor de integratiecontainer maken en in `secrets/api_token` zetten volgens `docs/beheer/integratiecontainer.md`. Binnen een minuut importeert de container de synthetische leden met de stub.
5. `docker compose -f docker-compose.yml -f compose.dev.yml exec worker flask seed` voor een synthetische loods (alleen buiten productie). Seed maakt geen leden: alleen de import via de API schrijft leden.
6. Een login aanmaken, zie hieronder.

De applicatie draait op http://localhost:8080. De API (`/api/v1`) is alleen bereikbaar via de interne Nginx-server op poort 8081, vanaf het netwerk `koppeling` (ADR-012).

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
- Controleren: `GET http://nginx:8081/api/v1/ik` met `Authorization: Bearer <token>`, vanaf het netwerk `koppeling`. Het contract staat in `app/api/openapi.yaml`.
- Uitzetten: `API_INGESCHAKELD=false` in `.env` en `docker compose up -d api`.

## Bijwerken

Een update met een nieuwe databaserol (zoals `botenloods_api` in slice 5): zet het wachtwoord in `.env` (`DB_API_WACHTWOORD`) en draai vóór `up` eerst `docker compose up -d db` en `docker compose exec db sh /docker-entrypoint-initdb.d/rollen.sh`. Na een wijziging die `web` of `api` opnieuw aanmaakt: `docker compose restart nginx`.

## Tests

- Unit en integratie: `docker compose -f docker-compose.yml -f compose.dev.yml run --rm test`
- E2E (stack moet draaien): `tests/e2e/draai.sh`, één test met `tests/e2e/draai.sh -k <naam>`. De hele suite draait per bestand, met 40 seconden pauze voor de rate limit op inloggen.

## Productie

`docker compose up -d` met `APP_OMGEVING=productie`, een `https://`-adres in `BASIS_URL` en het certificaat in `certs/` (`fullchain.pem`, `privkey.pem`). Het logo van de vereniging staat in `huisstijl/logo.png` (JPEG, PNG of WebP); na het vervangen `docker compose restart web`. Ontbreekt het of is het ongeldig, dan staat dat in `docker compose logs web` en toont de kopbalk alleen de naam.
