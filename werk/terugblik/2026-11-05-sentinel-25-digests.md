# Terugblik sentinel, review issue #25 (digests)

Datum: 2026-11-05. Taak: review van de gestagede diff op `fix/25-digests`.

## Wat ging goed

De brief noemde de vier vragen, het criterium met tekst en de bron (indexdigest van het geteste image). Daardoor was het oordeel per vraag te toetsen met `docker buildx imagetools inspect`.

## Wat kon beter

Of Dependabot `compose.dev.yml` en digestupdates bij een genegeerde versie oppakt, valt lokaal niet te toetsen. Dat blijft een aanname tot de eerste run op GitHub.

## Wat deed je zelf goed

Naast het bestaan van elke digest ook de inhoud gecontroleerd (`PYTHON_VERSION`, `PG_MAJOR`, versielabel), zodat vaststaat dat de digest bij het tag hoort en niet alleen in de repository bestaat. Ook `.github/workflows/` doorzocht: het Trivy-image staat al op een digest.

## Wat heb je onderweg verbeterd

Een eerste grep op `image:` vond niets door het patroon; met een ruimer patroon de compose-bestanden en de workflow alsnog gevonden.

## Wat kan structureel beter in de opdracht

Zet in de opdracht: "Noem bij een Dependabot-wijziging hoe na de merge wordt gecontroleerd dat elk manifest gevonden is (Insights, Dependency graph, Dependabot), en wie dat doet."
