# Terugblik forge: Traefik en beheerdocumentatie

**Datum:** 2026-10-31
**Taak:** ADR-013 bouwen (issue #29) en `documentatie/beheer/` schrijven (issue #30)

## Wat ging goed

De brief noemde de leidende bron, de toegestane afwijkingen en de images die lokaal stonden. Daardoor kon ik zonder vragen bouwen en wist ik bij elke keuze of ik moest stoppen. De tabel "Controles" in ADR-013 was direct bruikbaar als proeflijst.

## Wat kon beter

Een besluit van de stakeholder (images in ghcr.io, #35) kwam tijdens het werk binnen. Ik zag het pas bij de `git diff` vlak voor de oplevering en moest het voorbeeld met images daarna omzetten. Ook kostte de proef met 3,5 MB een omweg: Traefik sluit de verbinding terwijl de client nog stuurt, dus `urllib` meldt een reset in plaats van 413.

## Wat deed je zelf goed

Ik heb de productielabels apart getoond in een losse stack met een eigen Traefik en certificaat, naast de lokale stack. Zo zijn TLS, HSTS en de doorverwijzing van 80 aangetoond met de echte labels, en niet alleen met de lokale variant zonder TLS. De waarschuwing van Traefik over `aliasHeadersStrategy` heb ik met een proef op `X_Forwarded_For` nagelopen.

## Wat heb je onderweg zelf verbeterd

De integratiecontainer wacht nu op een gezonde `api`; anders gaf Traefik tijdens het starten 404 en volgde een uur pauze. De lokale Traefik kreeg een constraint, zodat hij de containers van de screenshotstack niet ziet.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Kijk aan het begin en halverwege met `git log --oneline` of er commits op de leidende bronnen zijn bijgekomen; een besluit dat tijdens het werk binnenkomt, verwerk je direct en meld je." En voor proeven op een grootte: "Een proef boven de grens van een proxy stuurt alleen de kop met `Content-Length`, niet het hele lichaam."
