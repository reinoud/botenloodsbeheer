# Terugblik aegis, herreview herstel release-workflow

Datum: 2026-11-03
Taak: herreview van het herstel in `.github/dependabot.yml` en `.github/workflows/images.yml` (#59, #61). Oordeel: akkoord.

## Wat ging goed

De opdracht noemde het eerdere punt, het gekozen herstel, de diff en de toetsvragen. Dat maakte de review kort. Actionlint draaide zonder fouten.

## Wat kon beter

Een release-run kan niet lokaal. Of `latest` en een prerelease de juiste tags krijgen, of `docker push --all-tags` slaagt en of de cache werkt, blijft daardoor onbewezen tot de eerste echte release.

## Wat deed je zelf goed

Ik heb het commentaar getoetst aan `pyproject.toml:29` en aan de overlay (regel 143) en de workflow stap voor stap nagelopen: één build, scan op dezelfde tag, push van alle lokale tags.

## Wat heb je onderweg zelf verbeterd

Ik heb gecontroleerd of er met `load: true` een provenance-attestatie wegvalt ten opzichte van de oude push-build. Dat is een adviespunt, geen blokkade, want #59 vraagt er niet om.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Na de eerste echte release controleert de regie met `docker buildx imagetools inspect` of elke verwachte tag bestaat en hetzelfde digest heeft, en zet de uitkomst in het issue."
