# botenloodsbeheer

Beheer van de botenloods van een kanovereniging. Projectregels: `docs/PROJECT-OVERLAY.md`. Architectuur: `docs/architecture/architectuur.md`.

## Lokaal starten

1. `cp .env.example .env`, `chmod 600 .env` en de geheimen invullen (uitleg staat in het bestand).
2. `docker compose -f docker-compose.yml -f compose.dev.yml up --build -d`
3. `docker compose -f docker-compose.yml -f compose.dev.yml exec worker flask seed` voor een synthetische loods (alleen buiten productie). Seed draait in de worker, omdat alleen die leden mag schrijven.
4. `docker compose -f docker-compose.yml -f compose.dev.yml exec web flask beheerder uitnodigen <gebruikersnaam>` en de link openen.

De applicatie draait op http://localhost:8080.

## Tests

- Unit en integratie: `docker compose -f docker-compose.yml -f compose.dev.yml run --rm test`
- E2E (stack moet draaien): `tests/e2e/draai.sh`, één test met `tests/e2e/draai.sh -k <naam>`

## Productie

`docker compose up -d` met `APP_OMGEVING=productie`, een `https://`-adres in `BASIS_URL` en het certificaat in `certs/` (`fullchain.pem`, `privkey.pem`).
