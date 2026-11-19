# Retrospective milestone 11 "Restpunten na v2.0.0"

Datum: 2026-11-19. Gesloten: #346 (importslot van de worker), #342 (logacties voor een kijker), #341 (eigen foutpagina voor 403 en 404), #290 (al opgelost door #298), #291 (`url()` in de CSS), #333 (grenstests voor de lidkeuze) en #347 (release v2.1.0). Input: de terugblikken van sentinel, prism, aegis en pipeline in `werk/terugblik/` van deze datum.

## Wat werkte

- De volgorde uit de milestone hield de kleine restpunten bij elkaar: vier issues gingen met één review van Sentinel door.
- Bij #341 lag het ontwerp van Design System er voordat Prism begon, en het besluit "403 houden" van de stakeholder ook. Er stond geen ontwerpvraag open tijdens de bouw.
- De release ging in één poging groen: unitsuite, trivy en twee E2E-runs. De les uit milestone 10 (native arm64 voor de E2E, een eigen tag voor trivy) werkte.

## Wat beter kan

- Een `app_errorhandler` draait zonder de hooks van het blueprint. Prism, Aegis en Design System vonden elk een gevolg daarvan (menumarkering, `no-store`, `g.beheerder`). Daardoor waren er bij #341 twee reviewrondes nodig.
- Reviewers moesten de acceptatiecriteria zelf met `gh issue view` ophalen.
- De brief voor de release-E2E zei "verse stack" maar niet hoe. Pipeline moest de opzet zelf afleiden, en `draai.sh` verving het token van de dev-stack.

## Waar de lessen landen

- Overlay v0.6.1: de acceptatiecriteria staan letterlijk in de reviewbrief.
- Overlay v0.6.2: een foutafhandelaar draait zonder hooks van het blueprint (Bouw); bij een nareview zegt de brief wat de vervangen guard nog afving, en de unitsuite draait in de achtergrond (Review).
- Overlay v0.6.3: de release-E2E draait in een eigen project met eigen images, en na `draai.sh` wordt de dev-integratie herstart.
