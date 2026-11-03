# ADR-005 Tokenontwerp voor de API

**Status:** Besloten door Foundation
**Datum:** 2026-10-30
**Versie:** v1.4.1
**Stories:** BLB-029 tot en met BLB-035, BLB-037

## Context

De externe API `/api/v1` is aan en uit te zetten en staat standaard aan. Ze levert plaatsen, boten, leden en wachtlijst, met een apart recht voor persoonsgegevens (intake), en sinds 2026-10-31 ook de import van leden voor de integratiecontainer (ADR-012). Ze is standaard niet vanaf internet bereikbaar (ADR-013). Er zijn persoonlijke tokens van een beheerder en robottokens zonder gebruiker, beide hooguit 3 jaar geldig. Per token zijn rechten en een IP-whitelist in te stellen; bij een robottoken is de whitelist verplicht. Een token dat binnen een maand verloopt, geeft een waarschuwing op de statuspagina. De API volgt dezelfde bedrijfsregels als de UI, met rate limiting en logging (overlay §6).

## Besluit

**Vorm en opslag.** Een token is `blb_` gevolgd door een prefix van 8 tekens en een geheim van 32 bytes uit `secrets`, base32. De database bewaart de prefix (voor weergave en opzoeken) en een SHA-256-hash van het hele token. Een trage hash zoals bcrypt is niet nodig: het geheim heeft 256 bits entropie. De applicatie toont de waarde één keer na aanmaken. Vergelijken gebeurt met `hmac.compare_digest`.

**Rechten.** Een vaste lijst in code: `plaatsen:lezen`, `boten:lezen`, `leden:lezen`, `wachtlijst:lezen`, `persoonsgegevens`, `leden:importeren` en `bootaantallen:lezen`. Een token heeft minstens één recht. Zonder `persoonsgegevens` geeft de domeinlaag naam en lidnummer, maar geen adres, telefoon of e-mail (BLB-032). `leden:importeren` is het enige schrijfrecht en hoort alleen bij het robottoken van de integratiecontainer (ADR-012). Het is alleen met de CLI te geven, niet in de tokenschermen (besluit stakeholder 2026-11-03, #52).

**Geldigheid.** `verloopt_op` is verplicht en ligt hooguit 3 jaar na aanmaken. Een persoonlijk token werkt niet meer zodra de beheerder geblokkeerd of verwijderd is. Een robottoken onthoudt wie het maakte, maar blijft werken als die beheerder vertrekt (BLB-031).

**IP-whitelist.** Een lijst van adressen en reeksen in CIDR-notatie, IPv4 en IPv6, opgeslagen als PostgreSQL `cidr[]` en bij invoer gevalideerd met `ipaddress`. Verplicht en niet leeg bij een robottoken, optioneel bij een persoonlijk token. De standaardwaarde bij aanmaken is het subnet van het netwerk `koppeling` (`KOPPELNET`). Het clientadres komt uit de header die Traefik zet; Flask vertrouwt via `ProxyFix` precies één proxy. Traefik vertrouwt geen binnenkomend `X-Forwarded-For` en zet het verbindingsadres, zodat een client het adres niet kan vervalsen (ADR-013). Dat geldt alleen voor verkeer via Traefik (issue #20).

**Controle per aanroep.** In deze volgorde: API aan, token bestaat en hash klopt, niet verlopen of ingetrokken, eigenaar actief (persoonlijk), IP in de whitelist, recht voor dit endpoint. Elke weigering geeft 401 of 403 zonder te verraden welke controle faalde, en een logregel van soort `api` met de tokennaam en reden. Een geslaagde aanroep geeft geen logregel en werkt alleen `laatst_gebruikt_op` bij (besluit stakeholder 2026-10-31).

**Robottoken maken.** Een robottoken ontstaat met `flask token robot` in `web` (ADR-012) of later in de tokenschermen. De CLI toont de waarde één keer.

**Persoonlijke tokens (slice 10).** Een persoonlijk token hoort bij de beheerder die het maakt (`beheerder_id`). Het krijgt elk recht behalve `leden:importeren`: een import hoort bij de integratiecontainer, niet bij een persoon. De whitelist is optioneel en het formulier vult `KOPPELNET` voor; een lege whitelist betekent elk adres (intake). In de praktijk werkt een persoonlijk token alleen met `compose.api-extern.yml`, want de router op `intern` laat alleen `KOPPELNET` door (ADR-013).

Blokkeren laat het token staan; de controle weigert dan met reden `eigenaar_inactief`, tot het account weer actief is. Verwijderen van de beheerder verwijdert diens persoonlijke tokens (`ON DELETE CASCADE`); de logregel van het verwijderen noemt het aantal in het veld `tokens`. Herstellen (ADR-001) laat de persoonlijke tokens staan (besluit stakeholder 2026-11-03); wie misbruik vermoedt, trekt ze in op `/tokens`. Een robottoken bewaart de naam van de maker, of `cli`, als tekst in `gemaakt_door`, zodat de maker zichtbaar blijft na vertrek (BLB-031).

**Tokenschermen.** Menu-item Tokens. Elke beheerder ziet en beheert alle tokens (BLB-035).

| Route | Recente inlog | Doet |
|-------|---------------|------|
| `GET /tokens` | nee | Naam, soort, eigenaar of maker, rechten, whitelist, vervaldatum, laatst gebruikt, ingetrokken op; nooit waarde of hash |
| `GET, POST /tokens/nieuw` | ja | Soort, naam, dagen (standaard 365), rechten, whitelist (verplicht bij robot). Het antwoord op de POST toont de waarde één keer, met `Cache-Control: no-store`, zonder redirect en zonder sessie |
| `POST /tokens/<id>/rechten` | ja | Nieuwe rechten, minstens één, geldig vanaf de volgende aanroep |
| `POST /tokens/<id>/intrekken` | ja | Elk token, ook van een ander |

Naam, whitelist en vervaldatum zijn niet te wijzigen: daarvoor maakt de beheerder een nieuw token.

**Log.** Elke handeling komt in het technische log (ADR-006), zonder waarde: `token.gemaakt` (nu ook met soort `persoonlijk` en de eigenaar), `token.rechten_gewijzigd` met `oud` en `nieuw`, en `token.ingetrokken`. `eigenaar_inactief` is een reden van `api.geweigerd`.

**Migratie 0009.** `token` krijgt `beheerder_id` (verwijzing met `ON DELETE CASCADE`, leeg bij robot) en `gemaakt_door` (tekst, verplicht, bestaande rijen `cli`), met de check `(soort = 'persoonlijk') = (beheerder_id IS NOT NULL)`. `botenloods_api` krijgt `SELECT (id, actief)` op `beheerder` en `SELECT` op `rek` en `plaats_bootsoort` (ADR-012). `botenloods_web` houdt zijn rechten op `token`. De cascade draait met de rechten van de eigenaar van de tabel, dus `web` heeft geen `DELETE` op `token` nodig (Probable; een test die als `web` een beheerder met token verwijdert, toont het aan).

**Rate limiting.** In Traefik met de middleware `ratelimit`, op de router van het entrypoint `intern` naar de dienst `api` (ADR-012, ADR-013): per token (sleutel is de hele `Authorization`-header) 60 aanroepen per minuut met een kleine burst, en per IP-adres een ruimere grens tegen aanroepen met willekeurige tokens. Overschrijding geeft 429 met `Retry-After` en een tekst, geen JSON. Traefik deelt de teller over alle Gunicorn-workers, anders dan een teller in het geheugen van Flask.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| JWT met handtekening | Intrekken vraagt toch een lijst in de database; geen voordeel bij één server |
| OAuth2 met client credentials | Autorisatieserver en tokenuitwisseling voor een handvol koppelingen |
| Token versleuteld opslaan | Terug te lezen waarde is een risico zonder nut; tonen kan maar één keer |
| Rate limiting met Flask-Limiter en Redis | Extra container voor wat Traefik al kan |
| Tekst in plaats van `cidr[]` | Werkt ook, maar de database controleert de vorm dan niet |

## Gevolgen

- De statuspagina toont tokens met `verloopt_op` binnen 31 dagen, met naam en datum, zonder waarde (BLB-037).
- Een gelekte database geeft geen bruikbare tokens.
- Achter een extra proxy van de hosting moet `ProxyFix` op twee hops; dat staat in `.env.example` als `PROXY_HOPS` met standaard 1. Een verkeerde waarde maakt de whitelist zinloos, dus aegis controleert dit bij elke installatiebeschrijving.
- Aegis reviewt tokens en de IP-controle vóór de commit (overlay §4).

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.4.1 | 2026-11-03 | `leden:importeren` alleen met de CLI | Besluit stakeholder 2026-11-03, issue #52 |
| v1.4.0 | 2026-11-03 | Persoonlijke tokens, tokenschermen, log en migratie 0009 | Ontwerp slice 10, issue #51 |
| v1.3.0 | 2026-10-31 | Rate limit en clientadres in Traefik; 429 als tekst | Besluit stakeholder 2026-10-31, issue #29 (ADR-013) |
| v1.2.1 | 2026-10-31 | Sleutel van de rate limit is de hele header, geen hash: core-Nginx kan niet hashen, en de header staat toch al in het geheugen van Nginx | Herstel slice 5, oordeel aegis (AEG-01) |
| v1.2.0 | 2026-10-31 | Geslaagde aanroepen niet in het log, weigeringen wel | Besluit stakeholder 2026-10-31 (backlog vraag 20) |
| v1.1.0 | 2026-10-31 | API standaard aan en niet alleen-lezen; rechten `leden:importeren` en `bootaantallen:lezen`; standaardwhitelist `KOPPELNET`; robottoken via de CLI; rate limit op de interne server | Besluiten stakeholder 2026-10-31, ADR-012 |
| v1.0.0 | 2026-10-30 | Eerste versie | |
