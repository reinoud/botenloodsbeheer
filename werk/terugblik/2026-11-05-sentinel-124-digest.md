# Terugblik sentinel: review digest python:3.14-slim (issue #124)

**Datum:** 2026-11-05
**Taak:** review vóór commit van de nieuwe digest in `docker/Dockerfile` en `integratie/Dockerfile`

## Wat ging goed

De brief noemde de digest, de Trivy-opties, de proefimages en de Python-versie. Daardoor kon ik direct op de proefimages toetsen, zonder zelf te bouwen.

## Wat kon beter

De brief zei niet welke platforms `images.yml` bouwt. Dat moest ik nagaan om te weten of een scan op alleen amd64 de criteria dekt (het is alleen `linux/amd64`).

## Wat deed je zelf goed

Ik heb Trivy zelf opnieuw gedraaid op beide images en met `dpkg-query` in de images gecontroleerd dat apt 3.0.4 er echt in zit. Zo is vastgesteld dat de proefimages van de nieuwe digest komen. Ook issuecommentaren heb ik via de API doorzocht, niet alleen de issueteksten.

## Wat heb je onderweg zelf verbeterd

De zoekopdracht naar de oude digest in issues heb ik uitgebreid naar alle commentaren, omdat `gh issue list` alleen de tekst van het issue doorzoekt.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: noem bij een review van een basisimage welke platforms `.github/workflows/images.yml` bouwt, zodat de reviewer weet welke architectuur de scan moet dekken.
