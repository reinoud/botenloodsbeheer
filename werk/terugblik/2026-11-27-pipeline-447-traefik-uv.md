# Terugblik pipeline: Traefik v3.7.18 en uv 0.13.8

**Datum:** 2026-11-27
**Taak:** controle van de updates uit #447 (Traefik) en #448 (uv) in de worktree `chore/447-448-dependabot`

## Wat ging goed

De opdracht noemde bestanden, regelnummers en de afspraak om bij een afwijking te stoppen. Daardoor was snel duidelijk welke proeven opnieuw moesten. De proxytest en de unitsuite (1856 geslaagd) liepen zonder hapering.

## Wat kon beter

De padproeven uit ADR-013 hebben geen script; ze zaten alleen als tekst in het ADR. Ik moest een losse proefopstelling bouwen. Ik startte zeven configuraties tegelijk, waardoor de tellingen van de rate limit een paar verzoeken uiteenlopen. Een eerste poging overschreef bovendien uitvoerbestanden door een naamsbotsing (`v3.7.1` voor 17 en 18).

## Wat deed je zelf goed

Ik vergeleek v3.7.17 en v3.7.18 met dezelfde verzoeken in vier configuraties, in plaats van alleen v3.7.18 te bekijken. Zo bleek dat het verschil beperkt is tot padparameters, en dat het een verbetering is voor de rate limit van `inloggen`. Ik gaf de unitsuite een eigen image-tag, zodat `botenloods-dev` van de regie niet werd overschreven.

## Wat heb je onderweg verbeterd

`documentatie/beheer/installatie.md` noemde nog "getest met v3.7.17"; dat staat nu op v3.7.18. Het commentaar in `tests/proxy/draai.sh` en ADR-013 (v1.5.3) zijn bijgewerkt. `docs/architecture/architectuur.md` regel 271 noemt v3.7.17 als historische proef en is bewust ongewijzigd.

## Wat kan structureel beter in de opdracht

Zet de padproeven uit ADR-013 in een script naast `tests/proxy/draai.sh`, zodat een Traefik-update ze met één commando herhaalt. Een `compose run test` met `image: botenloods-dev` hertagt het image van de regie; een override met een eigen tag lost dat op.

## Als regel die de regie letterlijk kan overnemen

Zet in de opdracht: voor de unitsuite op een proefimage een override-bestand in de scratchpad met `services.test.image: botenloods-dev:<tag>` en de conftest-mount, en het commando met `-f <override>`; bouw nooit zonder die override, want `botenloods-dev` is het image van de regie.
