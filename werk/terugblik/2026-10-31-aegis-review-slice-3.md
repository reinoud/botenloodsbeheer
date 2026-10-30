# Terugblik aegis, securityreview slice 3

**Datum:** 2026-10-31
**Taak:** securityreview van de gestagede wijziging van slice 3 (issue #13)

## Oordeel

**Akkoord.** Geen bevinding houdt de commit tegen.

## Wat ik controleerde

- **Logo-upload (ADR-008).** In de container met `afbeeldingen.verwerk(..., "logo")` getest. JPEG, PNG en WebP met EXIF (oriëntatie en een tekstveld), XMP en een PNG-tekstblok komen als PNG terug, zonder EXIF, XMP of tekstblok. Een PNG-kop van 7000 x 7000 en 1 x 40.000.001 pixels wordt geweigerd vóór het decoderen; 20.000 x 20.000 geeft de `DecompressionBombError` en de gewone foutmelding. SVG wordt geweigerd. Nginx staat 10 MB alleen toe op `location = /instellingen/logo`; de securityheaders blijven gelden, omdat de nieuwe location geen eigen `add_header` heeft.
- **Kleuren in CSS.** `huidig()` laat alleen `#rrggbb` door, bij het opslaan en bij het lezen (`app/domein/instellingen.py:26-28`). De naam komt niet in de stylesheet. `/huisstijl.css` is een bestand van dezelfde origin, dus `style-src 'self'` blijft ongewijzigd en er is geen nonce nodig. Ik vind de afwijking van ADR-002 veilig, en eenvoudiger dan een nonce. Wat de route openbaar maakt, zijn twee kleuren.
- **Toegang en recente inlog.** Zonder sessie geven `/instellingen`, `/vrij`, `/opgezegd`, `/leden/1`, `/leden?zoek=a` en `/indeling.xlsx` een 302 naar `/inloggen`; alleen `/huisstijl.css` geeft 200. De volgorde van de decorators is goed: eerst `inloggen_vereist`, daarna `recent_ingelogd`. De unittest `test_recente_inlog_vereist` draait met CSRF uit en controleert ook dat er geen rij is bijgekomen. Daarmee faalt het verzoek echt op de recente inlog en niet toevallig op iets anders. Beide formulieren nemen `_csrf.html` op; zonder token geeft een POST 400 (CSRFProtect).
- **Export.** Met namen die beginnen met `=`, `+`, `-`, `@`, een tab, een CR of een spatie bevat het blad nul `<f>`-elementen. Alle cellen zijn `inlineStr`, ook rek, bootnaam, lidnummer en de naam van de vereniging. Excel rekent een `inlineStr` nooit uit. De kolommen volgen intake regel 98: geen adres, telefoon, e-mail of foto.
- **Zoeken.** `icontains(..., autoescape=True)` maakt een geparametriseerde LIKE met ge-escapete `%` en `_`. Er is geen injectie.
- **Oud-leden.** `/opgezegd` en `/leden/<id>` tonen alleen naam, lidnummer, boten en opzegdatum, en alleen aan ingelogde beheerders.
- **Mutatielog.** Bij het opslaan worden oude en nieuwe naam en kleur gelogd, bij het logo alleen breedte en hoogte. Er staan geen geheimen of bestandsinhoud in het log. `migrations/env.py` (`NullPool`) raakt de security niet.

## Restpunten (houden de commit niet tegen)

| Ernst | Bestand en regel | Punt | Voorstel |
|-------|------------------|------|----------|
| laag | `docker/nginx/http.inc:12-15` | `$log_uri` laat `/leden?zoek=<naam>` ongemoeid, dus een gezochte ledennaam komt in de toegangslog (persoonsgegeven, overlay §8). | Voeg in de map de regel `~^/leden\?  /leden?...;` toe. |
| laag | `app/domein/instellingen.py:29` | `huidig()` laadt het hele logo (bytea) bij elke pagina en bij elk anoniem verzoek op `/huisstijl.css`, alleen om de sleutel te lezen. | Lees alleen `select(Afbeelding.sleutel).where(Afbeelding.id == ...)`. |
| laag | `docs/architecture/adr/ADR-002-frontendaanpak.md:17,22` | De ADR beschrijft nog een `<style>`-blok met nonce. | Foundation werkt de ADR bij naar `/huisstijl.css` (alleen hexkleuren, CSP ongewijzigd). |
| info | `app/domein/afbeeldingen.py:14` | `MAX_PIXELS` van 40 miljoen geldt ook voor het logo. Decoderen kost dan tot ongeveer 160 MB geheugen per verzoek, net als bij foto's. Dit risico bestond al; uploaden kan alleen een ingelogde beheerder met een recente inlog. | Geen actie nodig. Blijkt het geheugen krap, dan krijgt het logo een lagere grens. |

## Wat ging goed

De brief noemde de punten die ertoe doen (upload, CSS, routes, export, log) met bestanden en ADR's. Daardoor kon ik gericht controleren. De stack draaide al met de gestagede code, zodat ik in de container echt kon testen.

## Wat kon beter

De brief noemde `+`, `-`, `@`, tab en CR als risico voor formule-injectie. In xlsx speelt dat niet, alleen in csv. Ik heb het toch getest, zodat het gesloten is.

## Wat deed ik zelf goed

Ik heb niet alleen de code gelezen maar ook getest: metadata, decompressiebommen, SVG, de XML van het exportblad en anonieme toegang tot elke nieuwe route. Daarnaast heb ik nagegaan dat de unittest voor de recente inlog op de juiste controle faalt en niet toevallig, bijvoorbeeld op CSRF.

## Wat heb ik onderweg zelf verbeterd

Mijn eerste POST zonder sessie gaf 400. Dat kwam door CSRF, niet door de inlogcontrole. Daarom heb ik de inlogcontrole beoordeeld met de unittest met CSRF uit, die ook controleert dat er geen rij is bijgekomen.

## Wat kan structureel beter

Zet in de opdracht: "Komt er een nieuwe route met querystring of padparameter die persoonsgegevens kan bevatten, controleer dan de `$log_uri`-map in `docker/nginx/http.inc`."
