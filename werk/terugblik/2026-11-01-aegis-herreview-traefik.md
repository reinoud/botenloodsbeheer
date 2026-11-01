# Terugblik: herreview Traefik (#29), prioriteit van de router boten

Datum: 2026-11-01
Taak: herreview vóór commit van `boten.priority=500`, de aanvullingen in `documentatie/beheer/installatie.md` en het commentaar bij `VERSIE` in `.env.example`.

## Wat ging goed

De opdracht was smal en noemde precies wat getoetst moest worden, met het image en de vorm van de proef. De labels kwamen rechtstreeks uit `docker compose config`, dus de proef draaide op de gestagede tekst en niet op een overgetikte kopie. Vier starts van Traefik gaven elke keer dezelfde routering.

## Wat kon beter

De eerste stub (`python -m http.server`) leest geen body bij een POST. Traefik gaf daardoor 502 of 404 in plaats van een nette 200, wat als bewijs te zwak is. `docker compose config` weigerde eerst omdat de verplichte geheimen in `.env.example` leeg zijn; ik moest dummywaarden meegeven.

## Wat deed ik zelf goed

Ik heb eerst een positieve controle vastgelegd: een POST van 2 MB op `/` geeft 413 (web), op `/boten` 200 (boten), en 30 POST's op `/inloggen` geven precies 10 keer 429 (burst 20, dus router inloggen). Zo bewijst een 200 echt de router en niet een toevallige fout. De optie `aliasHeadersStrategy` heb ik in de helptekst van `traefik:v3.7.17` zelf opgezocht in plaats van uit het hoofd.

## Wat heb ik onderweg zelf verbeterd

Na de zwakke eerste ronde heb ik de stub vervangen door een klein script dat de body leest en 200 geeft, en de proef opnieuw gedraaid.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: gebruik voor een losse Traefik-proef een stub die de body leest en 200 geeft, en render de labels met `docker compose config` met dummywaarden voor de verplichte variabelen.
