# Retrospective mijlpaal slice 1 tot en met 11

**Datum:** 2026-11-03
**Mijlpaal:** slice 1 tot en met 11 gebouwd en gereviewd, securityronde na slice 11 (aegis en probe)
**Input:** de terugblikken in `werk/terugblik/` van 2026-10-30 tot en met 2026-11-03, en de rapporten in `werk/security/`

## Lessen

| Les | Waar geland |
|-----|-------------|
| De briefingchecklist is gegroeid tot 134 regels en overlapt op onderwerpen als mutanten, E2E en rate limits. Een lijst van die lengte wordt minder goed nagelopen. | Issue #71 (opschonen en groeperen per soort opdracht) |
| Een scan van afhankelijkheden alleen per mijlpaal vond Pillow 12.3.0 met bekende lekken pas na elf slices. Een release kan tussen twee rondes vallen. | Issue #59 (scan in de CI en Dependabot), vóór de eerste release (#35) |
| Een securityfix botste met de regel dat versies twee weken oud moeten zijn. De oplossing van pyasn1 moest wachten. | Overlay v0.3.21: datum naast `exclude-newer` leggen, wachten bij ernst laag of middel, besluit van de stakeholder bij ernst hoog |
| De DAST draaide deels op code uit de werkmap terwijl bedrock daar #58 bouwde. Het rapport moest daardoor melden tegen welke versie getest was. | Overlay v0.3.21: een DAST-stack zonder mounts van `app/` of vanuit een eigen worktree |
| Een rate limit van Traefik was te omzeilen met `%2F`. De proeven tot nu toe gebruikten alleen het gewone pad. | Issue #65; overlay v0.3.21: proeven op een rate limit gebruiken ook gecodeerde paden |
| Een test faalde sinds slice 9 in het image (`APP_VERSIE`) zonder eigen issue. Een bekende failure maakt de suite blind voor een nieuwe. | Issue #64 |
