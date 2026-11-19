# Retrospective milestone 10 "Kijkers en v2.0.0"

Datum: 2026-11-19. Gesloten: #322 (kijkers, Beheerders wordt Gebruikers) en #344 (release v2.0.0); #331 ging mee dicht, want #322 loste het op. Input: de terugblikken van apex, foundation, bedrock, sentinel en aegis bij #322 in `werk/terugblik/` en de scratchpad van de regie.

## Wat werkte

- Voorwerk vóór de bouw: intake, backlog, ADR-015 en de schermen van Design System (BV-91 tot en met BV-93) lagen vast voordat bedrock begon. De bouw had één open ontwerpvraag (het label op Boten), en die beantwoordde het ontwerp.
- Standaard weigeren met `KIJKER_TOEGESTAAN` en één test over alle routes: een nieuwe route zonder rolcontrole valt meteen op. Sentinel bewees dat met een eigen mutant.
- Reviewers controleerden met een positieve controle (4 logregels in de database, 2 voor de kijker) en niet met een lege pagina.
- De downgrade van migratie 0022 blokkeert kijkers eerst, zodat een terugstap geen kijker beheerder maakt.

## Wat beter kan

- Apex en foundation gingen ruim over hun woordbudget (1074 en 1129 bij 900) en hadden twee tot drie snoeirondes nodig.
- De E2E-basislijn in de brief was fout (55 uitkomsten bij 54 testfuncties); de reviewer moest per bestand narekenen.
- Bij de release draaide de E2E-stack eerst het amd64-image onder qemu. `uname -m` in de shell zegt x86_64 (Rosetta), Docker draait arm64. De regie bouwde het image voor trivy en tagde het als `latest`. Run 1 faalde met een 409 op de ledenimport en de worker haalde zijn healthcheck niet. Twee runs gingen verloren, ongeveer een uur.
- Bij dat onderzoek kwam #346 boven: de worker neemt elke 15 seconden het importslot, ook als de opschoning die dag al gedraaid heeft.

## Waar de lessen landen

- De lessen uit de terugblikken van #322 staan in `docs/PROJECT-OVERLAY.md` v0.5.98 en v0.5.99.
- Nieuw in v0.6.0 (E2E): de images voor trivy krijgen een eigen tag en nooit `latest`; de E2E-stack draait het native image (arm64), te controleren met `docker image inspect -f '{{.Architecture}}'`.
- Issue #346 (importslot van de worker), naar de volgende afstemming.
