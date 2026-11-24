# Terugblik Bedrock, 2026-11-24: race in de sessie door statische bestanden (#402)

## Wat ging goed
- De hypothese was met één curl te toetsen: `GET /static/menu.js` met een geldige sessie geeft `Set-Cookie`, zonder cookie niet. De oorzaak klopte.
- De opdracht noemde het sessiecookie, de testdatabase en het opruimen al, dus er was geen zoekwerk.

## Wat kon beter
- Ruff draait niet op de host en in de testcontainer faalt de cache (`/app/.ruff_cache`). Dat kostte twee pogingen.
- Mijn eerste E2E-lus schreef naar een relatief logpad dat niet bestond; de drie runs startten niet.

## Wat deed je zelf goed
- Proef met een eigen account (id en gebruikersnaam), cookie getekend met `get_signing_serializer`, en het account daarna met een delete op beide verwijderd.
- De test eerst zonder herstel laten falen (stash van `app/__init__.py`): alleen de statische test valt, de gewone pagina slaagt.

## Wat heb je onderweg verbeterd
- Een eerste testopzet met een ongebruikte inlogfunctie verwijderd; de test zet de sessie rechtstreeks met `session_transaction`.

## Wat kan structureel beter in de opdracht of de afspraken
- Zet in de opdracht: ruff draait in de testcontainer als `docker compose -f docker-compose.yml -f compose.dev.yml run --rm --no-deps test ruff check --no-cache app tests`, niet op de host.
- Zet in de opdracht: een E2E-lus in de achtergrond schrijft logs naar een absoluut pad in de scratchpad, en de opdracht noemt dat pad.
