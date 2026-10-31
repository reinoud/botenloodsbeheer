# Terugblik Aegis: securityreview slice 4 (issue #18)

Datum: 2026-10-31
Taak: securityreview van de gestagede wijziging van slice 4 (logo uit de installatie, migratie 0004).

## Oordeel en bevindingen

Oordeel: **akkoord**. Geen bevinding houdt de commit tegen.

Restpunten die de commit niet tegenhouden:

| Ernst | Bestand en regel | Punt |
|-------|------------------|------|
| laag | `app/domein/afbeeldingen.py:36` (`img.save(uit, "PNG")`) | Het ICC-profiel van het bronbestand blijft in de PNG van het logo staan. Getest met PNG, WebP en JPEG als bron: tekst, EXIF en GPS-velden verdwijnen, `icc_profile` blijft. ADR-008 zegt "als PNG zonder metadata". Het risico is beperkt: de installatiebeheerder levert het bestand en het logo is openbaar. Herstel: `img.save(uit, "PNG", icc_profile=None)`, met een unittest die nagaat dat `info` geen `icc_profile` meer bevat. De fotoroute (JPEG) heeft dit niet. |
| info | `app/web/huisstijl.py:47` en `docker/nginx/app.inc:4` | `X-Content-Type-Options: nosniff` staat twee keer in het antwoord. Dat is onschadelijk: browsers lezen de eerste waarde, en beide zijn `nosniff`. `/afbeelding` doet hetzelfde. De header in de route houdt de bescherming ook zonder Nginx; laten staan. |

## Wat ik heb getoetst

- **Logobestand als externe invoer.** In de webcontainer `logo_laden` aangeroepen met een ontbrekend bestand, een map, tekst met SVG-inhoud, een PNG-kop van 100.000 bij 100.000 pixels, een echte PNG van 42 megapixel, een bestand boven 10 MB, een afgekapte PNG, een symlink naar `/etc/passwd` en `/dev/null`. Elk geval geeft `None` en een waarschuwing in de log, zonder uitzondering en zonder dat web stopt. De leesgrens van `UPLOAD_MAX + 1` voorkomt dat een groot bestand in het geheugen komt. Een symlink kan alleen een bestand opleveren dat een geldige afbeelding is, en dat wordt opnieuw gecodeerd. Er lekt dus geen willekeurige bestandsinhoud. De map is alleen-lezen gekoppeld en het pad komt uit de configuratie van de installatie, niet van een gebruiker.
- **Route `GET /logo/<kenmerk>`.** Een juist kenmerk geeft 200, `image/png`, nosniff, de CSP van Nginx en een cache van een jaar. Een verkeerd kenmerk geeft 404 als platte tekst met `no-store`. Een pad met `..%2f` en een kenmerk van 5000 tekens worden door Nginx al met 400 geweigerd. De route vergelijkt alleen met het kenmerk in het geheugen; er is geen bestands- of databasetoegang op basis van invoer.
- **Verdwenen route.** `POST /instellingen/logo` geeft 404, een body van 2 MB krijgt 413 van Nginx (standaard 1 MB). In de code en de templates verwijst niets meer naar `logo_opslaan`, `logo_vervangen` of de sleutel `logo` in `instelling`.
- **Migratie 0004.** Alleen `DELETE` en een nieuwe CHECK-regel; geen `GRANT` of `REVOKE`. De rechten van `botenloods_web` blijven gelijk en zijn nog nodig voor foto's en naam en kleuren. Geen foreign key wijst naar een logo in `afbeelding`. Dat de downgrade het logo niet terugzet, staat in de docstring. Head en downgrade laat ik aan Sentinel.
- **Configuratie.** De worker krijgt `LOGO_BESTAND=None`. De migrate-dienst leest het logo niet, omdat Alembic `create_app` niet aanroept.

## Wat ging goed

De wijziging verwijdert meer dan ze toevoegt: een route met upload, een Nginx-locatie van 10 MB en een domeinfunctie zijn weg. De nieuwe route heeft geen invoer die verder komt dan een stringvergelijking. Dat maakt de review kort.

## Wat kon beter

De opdracht noemde "opnieuw coderen als PNG zonder metadata" als regel. Dat het ICC-profiel daarbij hoort, staat niet in ADR-008. Daardoor is het een interpretatie van mij, geen harde eis.

## Wat deed ik zelf goed

Elke controle draaide tegen de draaiende stack, met bestanden in een tijdelijke map in de container die zichzelf opruimt. Er is niets in de werkmap of de testmap gezet en de stack is niet herstart.

## Wat heb ik onderweg zelf verbeterd

Eerst ging ik ervan uit dat Pillow bij opnieuw opslaan alle metadata weglaat. Een gerichte test met tekst, EXIF en ICC in drie bronformaten liet zien dat het ICC-profiel blijft. Daarna heb ik de fotoroute ook nagelopen, om te zien of het punt breder speelt; dat is niet zo.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "ADR-008 'zonder metadata' betekent zonder EXIF, tekstblokken en ICC-profiel; de reviewer toetst dat met een bronbestand dat alle drie bevat."
