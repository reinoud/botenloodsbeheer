# ADR-002 Frontendaanpak

**Status:** Besloten door Foundation
**Datum:** 2026-10-30
**Versie:** v1.1.3
**Stories:** alle schermen, vooral BLB-016, BLB-020, BLB-021, BLB-027

## Context

De applicatie heeft ongeveer twintig schermen: overzichten, formulieren, een plaatsdetail, een openbare pagina en een printpagina voor kaartjes. Gebruikers zijn drie beheerders en bezoekers die een QR-code scannen. De interface moet werken van groot scherm tot telefoon. De huisstijl is per installatie instelbaar (intake, overlay §6). De stack is Python en Flask; er is geen frontendspecialist in het vaste team.

Het lastigste scherm is de indeling per rek (BLB-016): 160 plaatsen met status, leesbaar op een telefoon. Dat is een tabel of raster met kleuren, geen interactieve tekening.

## Besluit

De interface is server-rendered met Jinja-templates en gewone HTML-formulieren. Er is geen JavaScript-framework en geen build-stap.

- **Styling:** één CSS-bestand met design tokens als CSS custom properties (`--kleur-primair`, `--kleur-tekst`, `--ruimte-1`, `--radius` enz.). De tokens die de beheerder instelt (primaire en secundaire kleur) staan in een aparte stylesheet `/huisstijl.css` met alleen `:root`-variabelen, die de basistemplate na het vaste CSS-bestand laadt; de waarden zijn gevalideerd als hexkleur. De naam van de vereniging staat als tekst in de template. Geen enkele template bevat een vaste kleur.
- **Responsive:** mobile first met CSS grid en flexbox. Tabellen worden op smalle schermen kaarten per rij. De indeling per rek is een raster van plaatsen dat op een telefoon onder elkaar valt.
- **JavaScript:** alleen waar het niet anders kan: het passkeyscript (ADR-001), een kleine bevestiging bij verwijderen, en "alles selecteren" op de printpagina. Gewone bestanden in `static/`, zonder bundler.
- **Toegankelijkheid:** semantische HTML, labels bij elk veld, voldoende contrast. BLB-027 vraagt een waarschuwing bij slecht leesbare kleuren; de applicatie berekent het contrast volgens de WCAG-formule bij het opslaan.
- **Print:** de kaartjes zijn een HTML-pagina met print-CSS (`@page`, raster op A4). De beheerder print via de browser of slaat op als pdf (ADR-011).
- **CSP:** Traefik stuurt (ADR-013) een strikte Content Security Policy zonder inline scripts. Inline styles zijn niet nodig: de tokens komen uit `/huisstijl.css`, zodat de CSP geen nonce of uitzondering nodig heeft.

## Alternatieven

| Optie | Voordelen | Nadelen |
|-------|-----------|---------|
| SPA (React of Vue) met de API als backend | Rijke interactie; API wordt vanzelf gebruikt | Tweede codebasis, build-keten, node-afhankelijkheden, eigen auth-stroom in de browser; de API moet dan voor elk scherm schrijven, niet alleen voor de import van leden |
| Server-rendered met htmx | Deelupdates zonder herladen | Extra afhankelijkheid voor een gemak dat bij twintig schermen en drie gebruikers geen probleem oplost; later toe te voegen per scherm |
| CSS-framework (Bootstrap, Tailwind) | Snelle start | Vaste uitstraling of een build-stap; design tokens zijn met een eigen klein bestand eenvoudiger te sturen |
| Server-rendered, eigen CSS met tokens (gekozen) | Eén taal, één codebasis, geen build, snel op een telefoon, eenvoudig te testen met Playwright | Minder interactief; elke actie herlaadt de pagina |

## Gevolgen

- Een beheeractie is een formulier met CSRF-token en een redirect na verwerking (post/redirect/get). Meldingen van de domeinlaag (`Regelfout`) verschijnen als flashbericht.
- Het log onder een overzicht is een gedeelde template-macro (`_log.html`) die de regels voor het scherm toont. Overzichten tonen alleen bootmutaties; het technische log staat alleen op `/log/techniek`, onder een eigen menuoptie naast `/log`. Welk scherm welke regels toont en welke schermen geen log hebben (zoals `/indeling`), staat in ADR-006.
- Andere verenigingen passen de uitstraling aan via instellingen en het logobestand van de installatie (ADR-008), niet via eigen templates. Wie meer wil dan naam, kleuren en logo, vraagt een wijziging in de tokens.
- Komt er later behoefte aan deelupdates, dan is htmx per scherm toe te voegen zonder de aanpak te wijzigen. Dat besluit kan forge nemen.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.1.3 | 2026-11-01 | Twee logs: overzichten tonen alleen bootmutaties, technisch log onder een eigen menuoptie | Besluit stakeholder 2026-11-01, BLB-043, issue #38 |
| v1.1.2 | 2026-10-31 | CSP uit Traefik in plaats van Nginx | Besluit stakeholder 2026-10-31, issue #29 (ADR-013) |
| v1.1.1 | 2026-10-31 | Reden bij het alternatief SPA bijgewerkt (de API is niet meer alleen-lezen); logo uit de installatie | Besluiten stakeholder 2026-10-31 |
| v1.1.0 | 2026-10-31 | Tokens uit een aparte stylesheet `/huisstijl.css` in plaats van een `<style>`-blok met nonce | Slice 3 (issue #13); de CSP blijft ongewijzigd, beoordeeld door aegis |
| v1.0.0 | 2026-10-30 | Eerste versie | |
