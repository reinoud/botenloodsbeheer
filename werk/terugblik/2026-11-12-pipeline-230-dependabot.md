# Terugblik pipeline, #230 Dependabot docker-compose

Datum: 2026-11-12. Taak: oorzaak zoeken van "unknown error" bij docker-compose na 64c6d68.

## Wat ging goed
- Dependabot-CLI (via `go install` in de scratchpad) draaide direct met Docker; elke map afzonderlijk en beide samen via een jobbestand (`directories`, met en zonder `cooldown`) gaf exit 0.
- Bevestigd dat de parser beide bestanden leest: `compose.yml` levert socketproxy (ghcr.io) en traefik, `/` levert traefik en postgres.

## Wat kon beter
- De oorzaak is lokaal niet na te spelen; de CLI toont alleen de updater, niet de hosted-laag die de fout geeft. De opdracht had dat verschil kunnen noemen.
- De hostedlog is niet te lezen, dus het herstel is een hypothese, geen bewijs.

## Wat deed je zelf goed
- Jobbestand met `directories` en `cooldown` gebouwd, zodat de meerdere-mappen-vorm en de cooldown van de echte config zijn nagebootst.

## Wat heb je onderweg verbeterd
- Eerst de CLI-vlag `--directory` gebruikt (één map), daarna overgestapt op `-f` omdat alleen dat beide mappen in één job zet.

## Wat kan structureel beter
- Voor een wijziging in `.github/dependabot.yml` die een nieuwe map of vorm (`directories`) toevoegt: eerst als aparte, kleine PR meenemen en na de merge de eerstvolgende run in Insights, Dependabot controleren, zodat een fout aan één wijziging te koppelen is.

## Als regel voor de regie
Zet in de opdracht: bij een wijziging van `.github/dependabot.yml` die `directories` toevoegt of een map aan een bestaande ingang hangt, controleert de regie na de merge de eerstvolgende run per ecosysteem in Insights, Dependabot; bij een fout wordt de ingang gesplitst in één ingang per map.
