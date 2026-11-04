# Terugblik aegis, securityreview issue #91 (413-handler als app_errorhandler)

Datum: 2026-11-04. Taak: securityreview van de gestagede diff voor issue #91, gericht op de bredere werking van de handler.

## Wat ging goed

De brief noemde de plaats waar de 413 ontstaat (`app/__init__.py:60`), de routers met de middleware `3mb` en wat al eerder akkoord was. Daardoor kon ik de review beperken tot de nieuwe werking: alle paden van de dienst `api` in plaats van alleen paden met een view.

## Wat kon beter

De brief zei niet of de dienst `api` buiten Traefik bereikbaar is (gepubliceerde poorten, andere containers op `voorkant`). Dat heb ik zelf in `docker-compose.yml` nagekeken.

## Wat deed ik zelf goed

Ik heb de registratie in `create_app` gecontroleerd: de blueprint, en dus de app-brede handler, bestaat alleen als `DIENST` gelijk is aan `api`. Zo was de vraag over `web` met één regel code te beantwoorden, zonder test.

## Wat heb ik onderweg verbeterd

Eerst wilde ik een begrenzing van het weglezen voorstellen. Dat heb ik laten vallen: elke router naar `api` begrenst het lichaam op 3 MB, en wie Traefik omzeilt, kan ook zonder deze handler een worker bezighouden.

## Wat kan structureel beter

Zet in de opdracht: "Noem bij een review van een request-limiet of de dienst ook buiten Traefik bereikbaar is (gepubliceerde poort, gedeeld netwerk), en zo ja via welke route."
