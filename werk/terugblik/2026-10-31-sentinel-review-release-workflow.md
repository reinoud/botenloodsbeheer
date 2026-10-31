# Terugblik Sentinel: review release-workflow

**Datum:** 2026-10-31
**Taak:** review vóór commit van `.github/workflows/images.yml` (issue #35)

## Wat ging goed
De opdracht noemde het bestand, het issue, de besluiten en de Dockerfiles. Daardoor kon ik de matrix direct naast `docker-compose.yml` leggen.

## Wat kon beter
Het issue zegt "een prerelease krijgt geen latest", maar niet of dat het vinkje op GitHub of een achtervoegsel in de tag betekent. `metadata-action` kijkt alleen naar de tag.

## Wat deed ik zelf goed
Ik heb de build overgeslagen: de Dockerfiles zijn niet gewijzigd en compose bouwt ze al. Ik heb wel gecontroleerd dat `integratie/` een eigen `.dockerignore` heeft.

## Wat heb ik onderweg zelf verbeterd
Ik heb het verschil tussen het prerelease-vinkje en een semver-prerelease als advies gemeld en niet als blokkade, omdat het issue het niet eenduidig vastlegt.

## Wat kan structureel beter
Zet in de opdracht: bij een eis over prereleases staat erbij of het GitHub-vinkje of een tagachtervoegsel als `-rc1` bepalend is.
