# Bijwerken, tokens en logs

## Bijwerken

Een nieuwe versie start met dezelfde stappen als het voorbeeld dat de installatie volgt ([voorbeelden](voorbeelden.md)): `pull` of `--build`, en daarna `up -d`. `migrate` draait de databasemigraties vóór `web`, `api` en `worker` starten. Maak vóór elke update een back-up van de database; een migratie is niet altijd terug te draaien.

Vraagt een versie een nieuwe databaserol, zoals `botenloods_api`, zet dan eerst het wachtwoord in `.env` en maak de rol aan:

```sh
docker compose up -d db
docker compose exec db sh /docker-entrypoint-initdb.d/rollen.sh
```

Een herstart van Traefik is na een update niet nodig: hij volgt de containers via de labels. Wel aanbevolen na deze versie: de opties tegen gecodeerde tekens op de entrypoints (zie `installatie.md`); de applicatie weigert zo'n pad ook zelf met 400. Een nieuw logo: vervang `huisstijl/logo.png` en draai `docker compose restart web`.

## Tokens

- Beheerders maken, wijzigen en trekken tokens in op het scherm Tokens (`/tokens`), ook persoonlijke tokens; zie de handleiding.
- Maken met de CLI: `docker compose exec web flask token robot <naam> --recht leden:importeren --recht bootaantallen:lezen`. Het token verschijnt één keer. Zonder `--whitelist` geldt `KOPPELNET`, zonder `--dagen` 365 dagen, hooguit 1095.
- Vernieuwen: een nieuw token onder een andere naam maken, in `secrets/api_token` zetten en daarna het oude intrekken.
- Intrekken: `docker compose exec web flask token intrekken <naam>`.
- API uitzetten: `API_INGESCHAKELD=false` in `.env` en `docker compose up -d api web`.
- De statuspagina (`/status`) waarschuwt 31 dagen voordat een token verloopt, met naam en vervaldatum, en toont per robottoken de laatste aanroep.

## Logs

Elke dienst schrijft naar stdout: `docker compose logs <dienst>`. `web` en `api` schrijven per verzoek één toegangsregel, met adres, tijd, methode, pad, status en bytes:

```
10.203.0.4 [31/Oct/2026:18:25:46 +0100] "GET /api/v1/ik" 401 25
```

Het pad staat er zonder querystring, dus zonder zoektermen, en de code van een uitnodiging is vervangen door `/uitnodiging/...`. De healthcheck van Docker zelf staat er niet in.

Een weigering door Traefik, zoals een 429 van een rate limit of een 413 boven 3 MB op de API, komt in geen enkele log. De routers van de botenloods schrijven niets in de toegangslog van Traefik.

De toegangsregels bevatten IP-adressen. Bewaar de logs daarom niet langer dan nodig, en stem de bewaartermijn van logs en back-ups af op de termijn van 5 jaar voor gegevens van oud-leden.

## Bewaartermijn

De `worker` verwijdert elke dag na `OPSCHOON_TIJDSTIP` (standaard 04:00) de logregels van meer dan 5 jaar oud, en oud-leden van wie de opzegdatum meer dan 5 jaar geleden ligt, met hun boten en foto's. Zonder opzegdatum telt de datum waarop het lid uit de bron verdween. Een oud-lid met een boot op een plaats blijft staan. Loopt er op dat moment een import, dan probeert de opschoning het in de volgende ronde opnieuw, na 15 seconden. De worker gebruikt daarvoor de databaserol `botenloods_taken`, de enige rol die logregels mag verwijderen. Mislukt de opschoning, dan staat dat met de foutklasse op de statuspagina en volgt de volgende dag een nieuwe poging. De uitkomst staat ook in het technische log als `opschoning.uitgevoerd`.

Back-ups vallen buiten de applicatie. Een back-up bevat verwijderde gegevens tot hij zelf wordt verwijderd; bewaar back-ups daarom niet langer dan nodig.
