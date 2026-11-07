# Voorbeelden: images binnenhalen of zelf bouwen

Er zijn twee manieren om de images te krijgen. Beide gebruiken `docker-compose.yml` uit de repository, met een aanvulling uit `voorbeelden/`. De stappen uit [installatie](installatie.md) gelden voor beide.

## Kant-en-klare images

`voorbeelden/compose.images.yml` haalt de images op uit een registry en bouwt niets. Het komt naast `docker-compose.yml`. Op de host staan alleen `docker-compose.yml`, `compose.images.yml`, `docker/db-init.sh`, `.env`, `secrets/` en `huisstijl/`.

Bij elke release zet GitHub Actions de images openbaar in ghcr.io: `ghcr.io/reinoud/botenloods-app` en `ghcr.io/reinoud/botenloods-integratie`, alleen voor linux/amd64. Release `v1.2.3` geeft de tags `1.2.3`, `1.2` en `latest`. De eerste release is `v0.1.0`.

Haal de bestanden op bij de tag van de release, hier `v1.2.3`:

```sh
t=v1.2.3
u=https://raw.githubusercontent.com/reinoud/botenloodsbeheer/$t
mkdir -p docker secrets huisstijl
curl -fsSL -o docker-compose.yml $u/docker-compose.yml
curl -fsSL -o compose.images.yml $u/documentatie/beheer/voorbeelden/compose.images.yml
curl -fsSL -o .env.example $u/.env.example
curl -fsSL -o docker/db-init.sh $u/docker/db-init.sh
chmod +x docker/db-init.sh
```

Ontbreekt `docker/db-init.sh`, dan weigert `docker compose up` te starten met `bind source path does not exist`. Haal het bestand dan op en start opnieuw.

Zet in `.env` de versie, bijvoorbeeld `VERSIE=1.2.3`, en start:

```sh
c="docker compose -f docker-compose.yml -f compose.images.yml"
$c pull && $c up -d
```

## Bouwen uit een git-checkout

`voorbeelden/compose.git.yml` bouwt de images op de host en zet de versie, een git-tag, in hun naam. De vorige versie blijft zo staan om naar terug te gaan.

```sh
git clone https://github.com/reinoud/botenloodsbeheer.git botenloods
cd botenloods
git checkout <tag>
cp documentatie/beheer/voorbeelden/compose.git.yml .
VERSIE=<tag> docker compose -f docker-compose.yml -f compose.git.yml up -d --build
```

Terug naar de vorige versie is `git checkout` van die tag en `up -d` zonder `--build`, met de vorige `VERSIE`. Dat kan alleen als de nieuwe versie geen databasemigratie had; zie [bijwerken](bijwerken.md).
