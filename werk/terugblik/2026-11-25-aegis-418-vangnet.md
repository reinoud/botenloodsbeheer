# Terugblik Aegis, 2026-11-25

Taak: security-review van de gestagede diff voor #418 deel 2 (vangnet als aparte stack).

## Wat ging goed

De opdracht noemde de toetsvragen concreet: overschaduwing, de voorwaarde van `-vangnet-intern`, hardening, headers, certresolver en de docker-socket. Daardoor kon ik gericht lezen. Het image draaide los op 127.0.0.1 binnen een minuut, en de headers, het escapen en de gebruiker (65532) waren direct na te gaan.

## Wat kon beter

De vraag "kan een router van het vangnet een route van de app overschaduwen" dekt maar één richting. Het eigenlijke gat zat in de andere richting: paden waarvoor de app bewust geen router heeft (`/api/` op `websecure`). Die vallen nu bij het vangnet, ook als de app draait.

## Wat deed ik zelf goed

Ik heb de bevinding niet alleen uit de regels afgeleid. Ik heb haar bevestigd met een eigen Traefik met file-provider op een apart netwerk, met een positieve controle (`/` en `/inloggen` geven 200 van de "app") naast de afwijking (`/api/v1/ik` geeft 503). De stack `botenloods` bleef onaangeroerd.

## Wat heb ik onderweg zelf verbeterd

Eerst wilde ik de dev-stack gebruiken om de overlap te tonen. Dat zou de tests van een andere reviewer verstoren. Ik ben overgestapt op een losse Traefik met het healthpoort van het vangnet (8081, geeft 200) als nep-app, zonder docker-socket.

## Wat kan structureel beter

Zet in de opdracht: "Toets bij een router met lage prioriteit ook welke paden de app bewust níét routeert (zoals `!PathPrefix(/api/)` op `-web`) en of de nieuwe router die nu beantwoordt, terwijl de app draait."
