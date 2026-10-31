# Terugblik aegis, securityreview slice 5 (issue #19)

**Datum:** 2026-10-31
**Taak:** securityreview van de gestagede diff van slice 5 (API-dienst, robottoken, whitelist, rate limit, toegangslog)

## Wat ging goed

De brief noemde de vragen waar het risico zat. Daardoor kon ik elke vraag met een gerichte proef in de draaiende stack beantwoorden, met een eigen token en zonder de suites te draaien. De netwerken en de rechten in de database waren direct na te lopen met `docker network inspect` en `information_schema`.

## Wat kon beter

Mijn eerste proef gaf het token via stdin door aan `python -`, waarna Python het token als code las en het in een foutmelding toonde. Het ging om mijn eigen reviewtoken, dat ik daarna heb ingetrokken. Een container met een alleen-lezen rootfs accepteert ook geen `docker cp`; schrijven naar `/tmp` (tmpfs) via `sh -c 'cat > …'` werkt wel.

## Wat deed ik zelf goed

Bij elke weigering heb ik eerst een positieve controle gedaan. Hetzelfde token gaf 200 vanaf `koppeling` en 401 vanaf `achterkant`, dus de whitelist besliste en niet iets anders. Daarna gaf een direct verzoek aan `api:8000` met een vervalste `X-Forwarded-For` weer 200. Bij de rate limit liet ik eerst de echte aanroep slagen, daarna 70 vervalste aanroepen met alleen de prefix vanaf een ander adres, en toen gaf de echte aanroep 429.

## Wat heb ik onderweg verbeterd

Ik heb het token voortaan alleen uit een bestand met mode 0600 gelezen en het niet meer als argument of omgevingsvariabele meegegeven. Na afloop heb ik het token ingetrokken en de tijdelijke bestanden in de scratchpad en in de container verwijderd.

## Wat kan structureel beter

Zet in de opdracht: "Wijkt de bouwer af van een ADR op een securitycontrole (sleutel van de rate limit, adres voor de whitelist), dan toont hij met een proef dat de eigenschap uit de ADR blijft gelden, en anders legt hij de afwijking vóór de bouw aan foundation voor." En: "Geef de reviewer een container op het netwerk `koppeling` mee (bijvoorbeeld `docker run --rm -i --network botenloods_koppeling --entrypoint python botenloods-app`), zodat hij de whitelist en de rate limit met een positieve controle kan testen."
