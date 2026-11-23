# Retrospective milestone 14 "Integratie robuuster en v2.2.2"

Datum: 2026-11-23. Gesloten: #165 (al opgelost in #295 en #150, met bewijs gesloten), #374 (`draai.sh` zet het tokenbestand van de dev-stack terug), #372 (na een 404 van Traefik elke minuut opnieuw, hooguit vijf keer) en #377 (release v2.2.2). Input: de terugblikken van 2026-11-23 in `werk/terugblik/`.

## Wat werkte

- De release-E2E slaagde in één run (58 van 58) en was de eerste zonder tokenherstel op de dev-stack: #374 werkt.
- Aegis en Sentinel vonden naast elkaar drie verschillende lussen waarin de container de bron onbegrensd ophaalde. Elke vondst had een proef met getallen.
- Een systematische proef over alle herhalende patronen (1554 stuks) sloot de reeks af, waar losse gevallen dat niet deden.

## Wat beter kan

- #372 had vier reviewrondes nodig. Elk herstel dekte alleen het patroon van de vorige vondst. De systematische proef had in de eerste ronde gemoeten.
- Mijn commentaar met het besluit van de stakeholder kwam niet in #372: de opdracht faalde stil door een ongeldige optie en een weggefilterde foutmelding. Aegis zag het.
- Beide bouwagents stopten door een overbelaste API (529). Pipeline liet daardoor een tijdelijke kopie van `draai.sh` in de hoofdwerkmap achter.
- Pipeline zette bij #377 de waarden uit `.env` in zijn eigen uitvoer (dev-omgeving, niet in een bestand).
- Het opruimen van branches en het mergen liepen twee keer vast op de automatische modus; de stakeholder gaf daarna akkoord.

## Waar de lessen landen

- Overlay v0.6.20: unittests in een worktree, besluit eerst in het issue en controleren, pogingen of herhalingen, teller in een herhaallus met systematische proef, bewijs na het opruimen, `draai.sh` toetsen vanuit een worktree.
- Overlay v0.6.21: `.env` alleen op sleutels lezen, open verzoek in een proef, tijdstip na het opruimen.
- Een agent die stopt door een API-fout: de regie kijkt eerst naar de werkmap en de worktree voordat ze hervat. Dat deed de regie dit keer; geen nieuwe regel nodig.
- De override voor de release-E2E wordt elke release opnieuw gebouwd (terugblik pipeline bij #377). Dat landt in het voorstel voor de volgende milestone.
