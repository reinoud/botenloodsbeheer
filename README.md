# botenloodsbeheer

Beheer van de botenloods van een kanovereniging. Projectregels: `docs/PROJECT-OVERLAY.md`. Architectuur: `docs/architecture/architectuur.md`.

## Lokaal starten

1. `cp .env.example .env`, `chmod 600 .env` en de geheimen invullen (uitleg staat in het bestand).
2. `docker compose -f docker-compose.yml -f compose.dev.yml up --build -d`
3. `docker compose -f docker-compose.yml -f compose.dev.yml exec worker flask seed` voor een synthetische loods (alleen buiten productie). Seed draait in de worker, omdat alleen die leden mag schrijven.
4. `docker compose -f docker-compose.yml -f compose.dev.yml exec web flask beheerder uitnodigen <gebruikersnaam>` en de link openen.

De applicatie draait op http://localhost:8080. De API (`/api/v1`) is alleen bereikbaar via de interne Nginx-server op poort 8081, vanaf het netwerk `koppeling` (ADR-012).

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
