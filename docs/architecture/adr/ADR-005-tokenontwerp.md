# ADR-005 Tokenontwerp voor de API

**Status:** Besloten door Foundation
**Datum:** 2026-10-30
**Versie:** v1.2.1
**Stories:** BLB-029 tot en met BLB-035, BLB-037

## Context

De externe API `/api/v1` is aan en uit te zetten en staat standaard aan. Ze levert plaatsen, boten, leden en wachtlijst, met een apart recht voor persoonsgegevens (intake), en sinds 2026-10-31 ook de import van leden voor de integratiecontainer (ADR-012). Ze is niet vanaf internet bereikbaar. Er zijn persoonlijke tokens van een beheerder en robottokens zonder gebruiker, beide hooguit 3 jaar geldig. Per token zijn rechten en een IP-whitelist in te stellen; bij een robottoken is de whitelist verplicht. Een token dat binnen een maand verloopt, geeft een waarschuwing op de statuspagina. De API volgt dezelfde bedrijfsregels als de UI, met rate limiting en logging (overlay §6).

## Besluit

**Vorm en opslag.** Een token is `blb_` gevolgd door een prefix van 8 tekens en een geheim van 32 bytes uit `secrets`, base32. De database bewaart de prefix (voor weergave en opzoeken) en een SHA-256-hash van het hele token. Een trage hash zoals bcrypt is niet nodig: het geheim heeft 256 bits entropie. De applicatie toont de waarde één keer na aanmaken. Vergelijken gebeurt met `hmac.compare_digest`.

**Rechten.** Een vaste lijst in code: `plaatsen:lezen`, `boten:lezen`, `leden:lezen`, `wachtlijst:lezen`, `persoonsgegevens`, `leden:importeren` en `bootaantallen:lezen`. Een token heeft minstens één recht. Zonder `persoonsgegevens` geeft de domeinlaag naam en lidnummer, maar geen adres, telefoon of e-mail (BLB-032). `leden:importeren` is het enige schrijfrecht en hoort alleen bij het robottoken van de integratiecontainer (ADR-012).

**Geldigheid.** `verloopt_op` is verplicht en ligt hooguit 3 jaar na aanmaken. Een persoonlijk token werkt niet meer zodra de beheerder geblokkeerd of verwijderd is. Een robottoken onthoudt wie het maakte, maar blijft werken als die beheerder vertrekt (BLB-031).

**IP-whitelist.** Een lijst van adressen en reeksen in CIDR-notatie, IPv4 en IPv6, opgeslagen als PostgreSQL `cidr[]` en bij invoer gevalideerd met `ipaddress`. Verplicht en niet leeg bij een robottoken, optioneel bij een persoonlijk token. De standaardwaarde bij aanmaken is het subnet van het netwerk `koppeling` (`KOPPELNET`). Het clientadres komt uit de header die Nginx zet; Flask vertrouwt via `ProxyFix` precies één proxy. Nginx overschrijft `X-Forwarded-For` met `$remote_addr`, zodat een client het adres niet kan vervalsen.

**Controle per aanroep.** In deze volgorde: API aan, token bestaat en hash klopt, niet verlopen of ingetrokken, eigenaar actief (persoonlijk), IP in de whitelist, recht voor dit endpoint. Elke weigering geeft 401 of 403 zonder te verraden welke controle faalde, en een logregel van soort `api` met de tokennaam en reden. Een geslaagde aanroep geeft geen logregel en werkt alleen `laatst_gebruikt_op` bij (besluit stakeholder 2026-10-31).

**Robottoken maken.** Een robottoken ontstaat met `flask token robot` in `web` (ADR-012) of later in de tokenschermen. De CLI toont de waarde één keer.

**Rate limiting.** In Nginx met `limit_req`, op de interne server op poort 8081 die naar de dienst `api` doorstuurt (ADR-012): per token (sleutel is de hele `Authorization`-header als die de vorm van een token heeft; andere headers vallen alleen onder de grens per IP) 60 aanroepen per minuut met een kleine burst, en per IP-adres een ruimere grens tegen aanroepen met willekeurige tokens. Overschrijding geeft 429 met `Retry-After`. Nginx deelt de teller over alle Gunicorn-workers, anders dan een teller in het geheugen van Flask.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| JWT met handtekening | Intrekken vraagt toch een lijst in de database; geen voordeel bij één server |
| OAuth2 met client credentials | Autorisatieserver en tokenuitwisseling voor een handvol koppelingen |
| Token versleuteld opslaan | Terug te lezen waarde is een risico zonder nut; tonen kan maar één keer |
| Rate limiting met Flask-Limiter en Redis | Extra container voor wat Nginx al kan |
| Tekst in plaats van `cidr[]` | Werkt ook, maar de database controleert de vorm dan niet |

## Gevolgen

- De statuspagina toont tokens met `verloopt_op` binnen 31 dagen, met naam en datum, zonder waarde (BLB-037).
- Een gelekte database geeft geen bruikbare tokens.
- Achter een extra proxy van de hosting moet `ProxyFix` op twee hops; dat staat in `.env.example` als `PROXY_HOPS` met standaard 1. Een verkeerde waarde maakt de whitelist zinloos, dus aegis controleert dit bij elke installatiebeschrijving.
- Aegis reviewt tokens en de IP-controle vóór de commit (overlay §4).

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.2.1 | 2026-10-31 | Sleutel van de rate limit is de hele header, geen hash: core-Nginx kan niet hashen, en de header staat toch al in het geheugen van Nginx | Herstel slice 5, oordeel aegis (AEG-01) |
| v1.2.0 | 2026-10-31 | Geslaagde aanroepen niet in het log, weigeringen wel | Besluit stakeholder 2026-10-31 (backlog vraag 20) |
| v1.1.0 | 2026-10-31 | API standaard aan en niet alleen-lezen; rechten `leden:importeren` en `bootaantallen:lezen`; standaardwhitelist `KOPPELNET`; robottoken via de CLI; rate limit op de interne server | Besluiten stakeholder 2026-10-31, ADR-012 |
| v1.0.0 | 2026-10-30 | Eerste versie | |
