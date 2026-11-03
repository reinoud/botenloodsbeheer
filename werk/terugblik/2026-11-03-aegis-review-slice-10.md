# Terugblik aegis: securityreview slice 10 (#51)

**Datum:** 2026-11-03
**Taak:** securityreview van de gestagede diff van slice 10 tegen #51, ADR-001, ADR-005 v1.4.0, ADR-012 v1.6.0 en ADR-013 v1.2.0.
**Oordeel:** akkoord, met twee punten van ernst laag.

## Bevindingen

| ID | Ernst | Bestand:regel | Punt |
|----|-------|---------------|------|
| AEG-01 | laag | `documentatie/beheer/api-van-buiten.md:35` | Noemt niet wat er gebeurt achter een load balancer. `externtoegang` en `iprem` toetsen dan het adres van de load balancer: staat dat adres niet in `API_EXTERN_BRONNEN`, dan krijgt elke aanroep 403. Staat het er wel in, dan komt iedereen door en remt `iprem` alle clients samen. Voeg een zin toe naast die over `inlogrem` in `installatie.md:36` (`ipStrategy.depth=1` op beide middlewares, of de API niet van buiten openzetten). |
| AEG-02 | laag | `app/domein/tokens.py:69` | Via het web kan nu elke beheerder met een recente inlog een robottoken met `leden:importeren` maken, met elke whitelist. Met `compose.api-extern.yml` kan dat token dan ook van buiten importeren. Dat past bij ADR-005 §Persoonlijke tokens, maar ADR-005:16 zegt dat `leden:importeren` alleen bij het robottoken van de integratiecontainer hoort. De veiligheidsgrens, de recente inlog en het log beperken het risico. Foundation trekt de ADR-tekst recht, of de stakeholder kiest om dit recht alleen via de CLI toe te staan. Dit blokkeert de commit niet. |

## Wat ik heb gecontroleerd

- Recente inlog op `GET/POST /tokens/nieuw`, `POST /tokens/<id>/rechten` en `POST /tokens/<id>/intrekken`; `GET /tokens` zonder, zoals ADR-005 vraagt.
- CSRF via de proxy: alle drie de POST-routes geven zonder token 400, terwijl `GET /tokens` zonder sessie 302 geeft (de controle grijpt dus vóór de inlogcontrole). Er is geen token ingetrokken of gemaakt en de rechten zijn niet veranderd.
- Tokenwaarde: één keer in het antwoord, zonder redirect en zonder flash, met `no-store`. De waarde staat niet in `log.schrijf` en niet in de URL. In de schermafbeelding is hij gemaskeerd.
- Persoonlijk token: `leden:importeren` wordt geweigerd bij het maken en bij het wijzigen van rechten; de check op eigenaar actief zit vóór de whitelist; verwijderen werkt via de cascade. Bij herstellen en deblokkeren dekken de unittests het besluit van de stakeholder.
- Leesaanroepen via `traefik:8081` vanaf `koppeling`: met alle rechten 200 met de persoonsgegevens; met alleen `boten:lezen` en `wachtlijst:lezen` geven `plaatsen` en `leden` 403, en `boten` en `wachtlijst` alleen `lidnummer` en `naam` van de eigenaar.
- Migratie 0009 in de database: `botenloods_api` heeft `SELECT (id, actief)` op `beheerder` en `SELECT` op `rek` en `plaats_bootsoort`; `botenloods_web` houdt `SELECT, INSERT, UPDATE` op `token`; de check en de FK met cascade staan erop. De downgrade heb ik niet gedraaid.
- `compose.api-extern.yml` in een losse Traefik (eigen netwerken 10.232.x): 200 vanaf een adres in de bronnen en de whitelist (positieve controle), 403 vanaf een adres buiten de bronnen, 401 met vervalste `X-Forwarded-For`, `X-Real-Ip`, `Forwarded` en `X_Forwarded_For`. Per token 11 keer 200 en daarna 429 met `Retry-After`; per IP met nep-tokens 54 keer 401 en daarna 429. Zonder het bestand 404, en compose start niet als `API_EXTERN_BRONNEN` leeg is.

## Wat ging goed

Het ontwerp in de ADR's was precies genoeg om tegen te toetsen: routes, rechten, migratierechten en proeven stonden er per regel in. Het proefscript van forge kon ik met een eigen naam en eigen subnetten hergebruiken.

## Wat kon beter

De proef met 60 nep-tokens liep in een losse Traefik, maar tegen de gedeelde database. Daardoor staan er 54 regels `api.geweigerd` extra in het technische log terwijl sentinel testte. De melding van de regie over `draai.sh` kwam pas na mijn proeven; die proeven raakten de gedeelde proxy en het token van de integratiecontainer niet.

## Wat deed ik zelf goed

Elke weigering heb ik eerst afgezet tegen een positieve controle (200 met hetzelfde token vanaf het juiste adres, en 302 tegenover 400 bij CSRF). Ook heb ik gecontroleerd dat er geen bijwerking was. Mijn vier testtokens heb ik na afloop ingetrokken en de bestanden met de waarden verwijderd.

## Wat heb ik onderweg verbeterd

Voordat ik de losse Traefik startte, heb ik gecontroleerd dat de gedeelde Traefik een constraint op `botenloods_voorkant` heeft. Zonder die constraint hadden de gerenderde labels van de proef-api een tweede router op `intern` gekregen.

## Wat kan structureel beter in de opdracht

Zet in de opdracht: "Een proef met veel geweigerde aanroepen in een losse Traefik gebruikt een eigen database (`nieuwe_database`) of meldt vooraf aan de andere testers dat er regels `api.geweigerd` in het gedeelde log komen."
