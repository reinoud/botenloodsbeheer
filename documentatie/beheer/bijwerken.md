# Bijwerken, tokens en logs

## Bijwerken

Een nieuwe versie start met dezelfde stappen als het voorbeeld dat de installatie volgt ([voorbeelden](voorbeelden.md)): `pull` of `--build`, en daarna `up -d`. `migrate` draait de databasemigraties vóór `web`, `api` en `worker` starten. Maak vóór elke update een back-up van de database; een migratie is niet altijd terug te draaien.

Vraagt een versie een nieuwe databaserol, zoals `botenloods_api`, zet dan eerst het wachtwoord in `.env` en maak de rol aan:

```sh
docker compose up -d db
docker compose exec db sh /docker-entrypoint-initdb.d/rollen.sh
```

De indeling met rek, verdieping en vak (migratie 0011) verwijdert bij de upgrade alle bestaande rekken en plaatsen; boten blijven bestaan, zonder plaats. Dat is bedoeld voor een installatie zonder echte gegevens. Bouw de indeling daarna op in de webinterface, of met `docker compose exec worker flask seed` in een testomgeving (die leest `app/seed_rekken.csv` en `app/seed_indeling.csv`). De migratie heeft een werkende downgrade; de omschrijving van een rek vervalt daarbij.

Migratie 0012 voegt de tabel `verdieping_bootsoort` toe (de bootsoort die een beheerder bij Nieuw rek per verdieping kiest). Bestaande rekken en plaatsen veranderen niet. De downgrade verwijdert alleen de tabel; plaatsen houden hun bootsoorten.

Migratie 0013 trekt een ongebruikt recht van de webapplicatie op die tabel in. Er verandert niets aan gegevens of schermen.

Migratie 0015 (versie 0.3.0) haalt de instelbare kleuren weg: de app volgt vast de Dajaks-huisstijl. De downgrade zet de oude kleuren niet terug. Naam en logo blijven instelbaar. Migratie 0016 voegt de tabellen voor de bezettingsimport en de onthouden naamkoppelingen toe; bestaande gegevens veranderen niet. `docker-compose.yml` is in 0.3.0 gewijzigd: haal hem opnieuw op bij de tag. Compose start daarna niet als `docker/db-init.sh` ontbreekt (`installatie.md`).

Een herstart van Traefik is na een update niet nodig: hij volgt de containers via de labels. Wel aanbevolen na deze versie: de opties tegen gecodeerde tekens op de entrypoints (zie `installatie.md`); de applicatie weigert zo'n pad ook zelf met 400.

Migratie 0017 zet het logo in de database. Het logo in `huisstijl/logo.png` en de variabele `LOGO_BESTAND` doen niets meer; een bestaand logo moet één keer worden geüpload op Instellingen (blok Logo). Haal `docker-compose.yml` opnieuw op bij de tag: de koppeling van `./huisstijl` is eruit en er is een router voor `/instellingen/logo` bij. Daarna is een nieuw logo uploaden of verwijderen zonder herstart. De downgrade verwijdert een geüpload logo.

Versie 0.4.0 bevat migratie 0017 hierboven en migratie 0018. Migratie 0018 haalt adres, telefoon en e-mail van leden weg en het tokenrecht `persoonsgegevens`. Een actief token met alleen dat recht wordt ingetrokken, met een regel in het technische log; andere tokens verliezen alleen dat recht. De downgrade zet de kolommen leeg terug; de gegevens en het recht komen niet terug. `.env` kent nieuwe variabelen voor de koppeling met e-boekhouden (`EBOEKHOUDEN_USERNAME`, `EBOEKHOUDEN_CODE1`, `EBOEKHOUDEN_CODE2`, `BOOTAANTALLEN_SCHRIJVEN`), alleen nodig bij `LEDENBRON=eboekhouden` (`integratiecontainer.md`). `LOGO_BESTAND` kan uit `.env` weg.

## Tokens

- Beheerders maken, wijzigen en trekken tokens in op het scherm Tokens (`/tokens`), ook persoonlijke tokens; zie de handleiding.
- Maken met de CLI: `docker compose exec web flask token robot <naam> --recht leden:importeren --recht bootaantallen:lezen`. Het token verschijnt één keer. Zonder `--whitelist` geldt `KOPPELNET`, zonder `--dagen` 365 dagen, hooguit 1095. Een reeks breder dan /8 (IPv4) of /32 (IPv6) weigert de CLI.
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
