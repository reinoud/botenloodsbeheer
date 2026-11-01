# Terugblik foundation, issue #36

**Datum:** 2026-11-01
**Taak:** ADR-013 en architectuur §5 laten aansluiten op de bouw van Traefik (afwijkingen 1 tot en met 7 uit issue #36)

## Wat ging goed

Het issue, `werk/traefik-proeven.md` en de compose-bestanden gaven samen genoeg bewijs; elke afwijking was terug te vinden in de code. De optie `aliasHeadersStrategy` heb ik opgezocht in `traefik:v3.7.17 --help` van het lokale image, zodat de naam in ADR en beheerdocumentatie klopt.

## Wat kon beter

`documentatie/beheer/voorbeelden/traefik/compose.yml` is een compose-bestand in de documentatie. De opdracht verbood compose wijzigen, dus de nieuwe eis staat nog niet in het voorbeeld. Dat moet iemand anders doen.

## Wat deed ik zelf goed

Vóór de wijziging aan `openapi.yaml` gecontroleerd welke test het bestand leest (`test_openapi_is_geldig_en_beschrijft_elke_route`, alleen geldigheid en paden) en daarna de spec gevalideerd in het image `botenloods-dev`.

## Wat heb ik onderweg zelf verbeterd

De ADR noemde voor de proef op `X-Forwarded-For` alleen die kop; ik heb de varianten uit de proef (`X_Forwarded_For`, `X-Real-Ip`, `Forwarded`) toegevoegd, zodat de nieuwe eis en de proef bij elkaar passen.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Voorbeeldbestanden in `documentatie/` (zoals `voorbeelden/traefik/compose.yml`) gelden als documentatie en mag je bijwerken, of: gelden als compose en laat je staan."
