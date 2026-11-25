# Terugblik pipeline, #418 deel 2 (vangnet)

Datum: 2026-11-25. Taak: het vangnet inbouwen als aparte stack, met E2E, unittest, Dependabot, Trivy en documentatie.

## Wat ging goed

De opdracht was concreet: bronnen in volgorde, ontwerpkeuzes vooraf, en een vast eindformaat. Daardoor hoefde ik niets te vragen. De drie routes naar een oplossing (override, shellscript, unittest) lagen vast en pasten op de bestaande structuur.

## Wat kon beter

De opdracht noemde niet dat de integratiecontainer alleen de platte 404 van Traefik herkent (`integratie/koppeling/__init__.py`, `TRAEFIK_404`). Een 503 van het vangnet telt daar als gewone fout met een uur wachttijd. Dat vond ik pas bij het schrijven van de documentatie. Een eerste E2E-run faalde op een time-out vlak na `stop web`: Traefik stuurt kort naar een gestopte container.

## Wat deed je zelf goed

Ik heb de test eerst laten falen met een mutant (vangnet op prioriteit 100000, en `-intern` op 5000) voordat ik groen meldde. Ik draaide de E2E vijf keer en controleerde na elke run met `docker ps` dat `web` en `api` weer healthy waren en dat er geen vangnetcontainer bleef staan.

## Wat heb je onderweg zelf verbeterd

De wachtlus in `test_fase.py` ving alleen `AssertionError`; nu ook `OSError`, na de time-out in run 2. De trap in `vangnet.sh` start web en api altijd weer, haalt het vangnet weg en wacht tot beide healthy zijn. Router `-vangnet` kreeg dezelfde `tls.certresolver` als de app, zodat het vangnet een certificaat kan krijgen als de app nog nooit heeft gedraaid.

## Wat kan structureel beter in de opdracht of afspraken

- Zet in de opdracht: bij elke wijziging aan wat een client van Traefik ziet (404, 503, headers), zoek in `integratie/` en `tests/` naar de code die op dat antwoord reageert, en noem die vooraf.
- Zet in de opdracht: een E2E-stap die containers stopt, wacht met een lus die ook verbindingsfouten opnieuw probeert, en herstelt in een trap.
