# ADR-005 Tokenontwerp voor de API

**Status:** Besloten door Foundation
**Datum:** 2026-10-30
**Stories:** BLB-029 tot en met BLB-035, BLB-037

## Context

De externe API `/api/v1` is aan en uit te zetten en in de eerste versie alleen-lezen: plaatsen, boten, leden en wachtlijst, met een apart recht voor persoonsgegevens (intake). Er zijn persoonlijke tokens van een beheerder en robottokens zonder gebruiker, beide hooguit 3 jaar geldig. Per token zijn rechten en een IP-whitelist in te stellen; bij een robottoken is de whitelist verplicht. Een token dat binnen een maand verloopt, geeft een waarschuwing op de statuspagina. De API volgt dezelfde bedrijfsregels als de UI, met rate limiting en logging (overlay §6).

## Besluit

**Vorm en opslag.** Een token is `blb_` gevolgd door een prefix van 8 tekens en een geheim van 32 bytes uit `secrets`, base32. De database bewaart de prefix (voor weergave en opzoeken) en een SHA-256-hash van het hele token. Een trage hash zoals bcrypt is niet nodig: het geheim heeft 256 bits entropie. De applicatie toont de waarde één keer na aanmaken. Vergelijken gebeurt met `hmac.compare_digest`.

**Rechten.** Een vaste lijst in code: `plaatsen:lezen`, `boten:lezen`, `leden:lezen`, `wachtlijst:lezen` en `persoonsgegevens`. Een token heeft minstens één recht. Zonder `persoonsgegevens` geeft de domeinlaag naam en lidnummer, maar geen adres, telefoon of e-mail (BLB-032). Schrijfrechten komen pas met een latere story.

**Geldigheid.** `verloopt_op` is verplicht en ligt hooguit 3 jaar na aanmaken. Een persoonlijk token werkt niet meer zodra de beheerder geblokkeerd of verwijderd is. Een robottoken onthoudt wie het maakte, maar blijft werken als die beheerder vertrekt (BLB-031).

**IP-whitelist.** Een lijst van adressen en reeksen in CIDR-notatie, IPv4 en IPv6, opgeslagen als PostgreSQL `cidr[]` en bij invoer gevalideerd met `ipaddress`. Verplicht en niet leeg bij een robottoken, optioneel bij een persoonlijk token. Het clientadres komt uit de header die Nginx zet; Flask vertrouwt via `ProxyFix` precies één proxy. Nginx overschrijft `X-Forwarded-For` met `$remote_addr`, zodat een client het adres niet kan vervalsen.

**Controle per aanroep.** In deze volgorde: API aan, token bestaat en hash klopt, niet verlopen of ingetrokken, eigenaar actief (persoonlijk), IP in de whitelist, recht voor dit endpoint. Elke weigering geeft 401 of 403 zonder te verraden welke controle faalde, en een logregel van soort `api` met de tokennaam en reden. Een geslaagde aanroep geeft een logregel met endpoint en status en werkt `laatst_gebruikt_op` bij.

**Rate limiting.** In Nginx met `limit_req`: per token (sleutel is een hash van de `Authorization`-header) 60 aanroepen per minuut met een kleine burst, en per IP-adres een ruimere grens tegen aanroepen met willekeurige tokens. Overschrijding geeft 429 met `Retry-After`. Nginx deelt de teller over alle Gunicorn-workers, anders dan een teller in het geheugen van Flask.

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
