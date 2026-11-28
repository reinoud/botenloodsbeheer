Datum: 2026-11-28. Taak: issue #454, padproeven van ADR-013 als script naast `tests/proxy/draai.sh` (pipeline).

## Wat ging goed

- De bestaande opzet droeg het werk: `klant.py` (client in een container met vast adres), de digest in `compose.traefik.yml` en het patroon `controle` met een lijst mislukte controles. Er kwam geen framework bij.
- `web` uit `docker-compose.yml` gaat met zijn eigen labels de proef in (`compose.pad.yml` vervangt alleen het commando). De routers en middlewares zijn dus die van productie, en de proef kan niet afwijken van de labels.
- Een positieve controle vóór elke "geen rem" en elke 400 (GET `/inloggen` is 200, POST `/inloggen` geeft 429) voorkomt dat een lege uitkomst als bewijs telt.

## Wat kon beter

- De eerste versie van `rem` eiste "20 keer 200, dan 429". Dat hangt af van de tijd sinds de vorige proef op dezelfde router (`/inloggen` en `/uitnodiging` delen één teller) en gaf een foutmelding bij `/uitnodiging`. Ik heb dat pas na een volledige run gezien.
- Ik startte een tweede run terwijl de eerste nog in de achtergrond liep (de melding "niet voltooid binnen 120 s" las ik als afgebroken). Die twee liepen over elkaar heen en ik moest opruimen en opnieuw draaien.
- De 400 van Traefik voor een gecodeerd teken heeft een leeg lichaam, terwijl `klant.py` "Bad Request" verwachtte. De opdracht noemde dat niet; het bleek pas bij de eerste run.

## Wat deed je zelf goed

- Elke verwachting vergeleken met `werk/traefik-proeven.md` (herhaling v3.7.18) in plaats van de gemeten uitkomst over te nemen. Zo kwam alleen `%2f` naar `%2F` (Traefik schrijft de hexcijfers hoofdletter) als nieuwe uitkomst naar boven, en die staat nu in het script met een reden.
- Vier rondes met een nieuwe Traefik (opties voor gecodeerde tekens uit, aan, uit, aan), zodat de routeringsproef na minstens drie herstarts telt (overlay, Security en proxy).
- Geen `rm` in het script (geen tijdelijk bestand): uitvoer van `up` gaat in een variabele.

## Wat heb je onderweg zelf verbeterd

- `rem` van een vaste burst naar "429 aanwezig" (ja) of "25 keer 200" (nee).
- `TRAEFIK` in `klant.py` kent per status meerdere toegestane lichamen; `draai.sh` ziet daar geen verschil van (zie de run).
- Gecodeerde opties op `websecure` in `compose.traefik.yml` via `PROEF_GECODEERD`, met `true` (de standaard van Traefik) als terugval, zoals `PROEF_PROXYPROTOCOL`.

## Wat kan structureel beter in de opdracht of de afspraken

- Zet in de opdracht: "Een run van een proefscript langer dan twee minuten draait met `run_in_background` en één agent wacht met een until-lus op het einde; start nooit een tweede run van hetzelfde script zolang `pgrep -f <script>` nog iets toont."
- Zet in de opdracht: "Een rate-limitproef die op de burst rekent, noemt of routers een teller delen en wat de tijd sinds de vorige proef doet; kies bij twijfel 'er komt een 429' in plaats van 'na precies N'."
- Zet in de opdracht: "Noem het lichaam en de Content-Type van de 400, 403, 404 en 429 van Traefik voor deze versie; ze verschillen per optie."
