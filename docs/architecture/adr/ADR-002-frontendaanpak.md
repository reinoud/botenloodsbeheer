# ADR-002 Frontendaanpak

**Status:** Besloten door Foundation
**Datum:** 2026-10-30
**Versie:** v1.2.4
**Stories:** alle schermen, vooral BLB-016, BLB-020, BLB-021, BLB-027

## Context

De applicatie heeft ongeveer twintig schermen: overzichten, formulieren, een plaatsdetail, een openbare pagina en een printpagina voor kaartjes. Gebruikers zijn drie beheerders en bezoekers die een QR-code scannen. De interface moet werken van groot scherm tot telefoon. De huisstijl is vast: de Dajaks-basis (besluit stakeholder 2026-11-06, issue #150). Alleen de naam en het logo zijn per installatie te kiezen. De stack is Python en Flask; er is geen frontendspecialist in het vaste team.

Het lastigste scherm is de indeling per rek (BLB-016): 160 plaatsen met status, leesbaar op een telefoon. Dat is een tabel of raster met kleuren, geen interactieve tekening.

## Besluit

De interface is server-rendered met Jinja-templates en gewone HTML-formulieren. Er is geen JavaScript-framework en geen build-stap.

- **Styling:** de tokens en componenten komen uit de Dajaks-basis 0.3.0, afgenomen met `basis/afname.py` in `app/web/static/ds/` (met `ds-manifest.json`). De aanvulling `dj-components.css` staat niet in de afname en is gekopieerd naar `app/web/static/dj/`, zodat de conformiteitscontrole van de basis slaagt. Laadvolgorde: `ds/tokens/dajaks.css`, `ds/ds-components.css`, `dj/dj-components.css`, `stijl.css`. Templates gebruiken `ds-` en `dj-` klassen. `stijl.css` bevat alleen wat de basis niet kent (de `bl-`klassen van blok 1: pagina, kop en menu, rekraster en indelingsformulier; printkaartjes, `.qr`, `.foto` en log) en gebruikt alleen `var(--token)` en geen vaste kleur. Een `.ds-` of `.dj-` klasse komt alleen voor onder een `bl-`klasse als producthaak, nooit als losse selector. Rubik en PT Sans komen als woff2 uit `/static`, zonder externe bron. Alleen het lichte thema; de kaartjes blijven licht. De kleuren zijn niet instelbaar: `/huisstijl.css` en de kleurkiezers zijn vervallen. De naam van de vereniging staat als tekst in de template.
- **Responsive:** mobile first met CSS grid en flexbox. Tabellen worden op smalle schermen kaarten per rij. De lijsten Boten, Leden, Opgezegd, Gaan opzeggen en Wachtlijst zijn geen tabel maar een `ul.bl-lijst` met per item titel, subregel en zijkant (lijstpatroon 1B, BV-46); alleen de importruns op Leden blijven een tabel. Elke lijst heeft een zoekveld met een zichtbare knop en het aantal erboven; het zoeken is een "bevat" zonder onderscheid in hoofdletters of accenten (`jose` vindt `José` en andersom): kolom en zoektekst gaan door de functie `unaccent` van de PostgreSQL-extensie `unaccent`, die migratie 0021 aanmaakt (de extensie is vertrouwd, dus de eigenaar van de database volstaat; de rollen web, api en worker hebben geen extra recht nodig en `docker/db-init.sh` blijft gelijk; de escape van `%`, `_` en `\` komt na `unaccent`). Boten en Wachtlijst hebben daarnaast het soortfilter (`bootsoort`). Een genormaliseerde kolom is niet gekozen: die moet bij elke schrijfweg en bij de import worden bijgehouden. Het raster van een rek (indeling en rekoverzicht) schuift op een telefoon horizontaal, met een vaste kolom voor de verdieping. Het Rekoverzicht (`/rekoverzicht`, alleen beheerders) toont dat raster met een plaatje per plaats uit `static/boten/`; een bootsoort zonder plaatje toont de naam als tekst, en de alt-tekst noemt plaatscode, bootsoort en status.
- **JavaScript:** alleen waar het niet anders kan: het passkeyscript (ADR-001). Verwijderen vraagt geen bevestiging (BV-60). Het filter op `/vrij` werkt zonder script: de knop **Toon vrije plaatsen** is er altijd en de keuzelijst verstuurt niet zelf (WCAG 3.2.2). Dit vervangt issue #99 (filter zonder knop, gesloten). De keuzepagina voor kaartjes (`/kaartjes`) werkt zonder script: de selectievakjes **Alle plaatsen** en **Heel <rek>** laten de server de plaatsen bepalen (ADR-011). Gewone bestanden in `static/`, zonder bundler.
- **Toegankelijkheid:** semantische HTML, labels bij elk veld, voldoende contrast. De kleurparen van de basis zijn getoetst door het design system; een waarschuwing bij slecht leesbare kleuren is niet meer nodig. Tabellen worden onder 40rem kaarten (`dj-table--stack`) met `data-label` op elke `td` en ARIA-rollen op tabel, rij en cel.
- **Print:** de kaartjes zijn een HTML-pagina met print-CSS (`@page`, raster op A4). De beheerder print via de browser of slaat op als pdf (ADR-011).
- **CSP:** Traefik stuurt (ADR-013) een strikte Content Security Policy zonder inline scripts. Inline styles zijn niet nodig: alle stijl staat in bestanden onder `/static`, zodat de CSP geen nonce of uitzondering nodig heeft.

## Alternatieven

| Optie | Voordelen | Nadelen |
|-------|-----------|---------|
| SPA (React of Vue) met de API als backend | Rijke interactie; API wordt vanzelf gebruikt | Tweede codebasis, build-keten, node-afhankelijkheden, eigen auth-stroom in de browser; de API moet dan voor elk scherm schrijven, niet alleen voor de import van leden |
| Server-rendered met htmx | Deelupdates zonder herladen | Extra afhankelijkheid voor een gemak dat bij twintig schermen en drie gebruikers geen probleem oplost; later toe te voegen per scherm |
| CSS-framework (Bootstrap, Tailwind) | Snelle start | Vaste uitstraling of een build-stap; design tokens zijn met een eigen klein bestand eenvoudiger te sturen |
| Server-rendered, eigen CSS met tokens (gekozen) | Eén taal, één codebasis, geen build, snel op een telefoon, eenvoudig te testen met Playwright | Minder interactief; elke actie herlaadt de pagina |

## Gevolgen

- Een beheeractie is een formulier met CSRF-token en een redirect na verwerking (post/redirect/get). Meldingen van de domeinlaag (`Regelfout`) verschijnen als flashbericht.
- Het log onder een overzicht is een gedeelde template-macro (`_log.html`) die de regels voor het scherm toont. Overzichten tonen alleen bootmutaties; het technische log staat alleen op `/log/techniek`, onder een eigen menuoptie naast `/log`. Het log heeft de vorm 3B (BV-46): onder een overzicht een dicht uitklapblok **Log**, op de logpagina zelf zonder uitklapblok, met per dag een kop met de weekdag en per mutatie een regel. De dag volgt de tijdzone van de installatie, niet UTC. Welk scherm welke regels toont en welke schermen geen log hebben (zoals `/indeling`), staat in ADR-006.
- Andere verenigingen kiezen naam en logobestand (ADR-008), niet de kleuren. Wie een andere uitstraling wil, neemt een andere basis af; de afname is een kopie met manifest en conformiteitstest.
- Komt er later behoefte aan deelupdates, dan is htmx per scherm toe te voegen zonder de aanpak te wijzigen. Dat besluit kan forge nemen.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.2.4 | 2026-11-11 | Zoeken zonder onderscheid in accenten via de extensie `unaccent` (migratie 0021) | Issue #232 |
| v1.2.3 | 2026-11-07 | Blok 3A: lijsten Boten, Leden, Opgezegd, Gaan opzeggen en Wachtlijst als `ul.bl-lijst` met zoeken en filters; log 3B (uitklapblok, kop per dag in de tijdzone van de installatie); de bevestiging bij verwijderen bestaat niet en is uit de tekst gehaald | Besluiten stakeholder BV-46, BV-47 en BV-60, issue #150 |
| v1.2.2 | 2026-11-07 | Scherm Vrije plaatsen: zichtbare knop in plaats van een script bij de keuze, `vrij.js` vervalt, aantal boven het resultaat | Besluit stakeholder BV-44, issue #150 (vervangt issue #99) |
| v1.2.1 | 2026-11-07 | Blok 1 van het nieuwe ontwerp: menu in drie groepen, `bl-`klassen voor het rekraster, het raster schuift op een telefoon; `ds-` en `dj-` klassen alleen onder een `bl-`klasse | Besluiten stakeholder 2026-11-06 (BV-42), issue #150 |
| v1.2.0 | 2026-11-06 | Dajaks-basis 0.3.0 met `ds-` en `dj-` klassen en eigen woff2; alleen licht thema; instelbare kleuren en `/huisstijl.css` vervallen | Besluiten stakeholder 2026-11-06, issue #150 |
| v1.1.5 | 2026-11-05 | JavaScript zoals gebouwd: alles selecteren op de kaartjespagina zonder script, filter op `/vrij` met script | Issue #47 (slice 8), issue #99 |
| v1.1.4 | 2026-11-04 | Scherm Rekoverzicht met plaatjes per plaats | Besluiten stakeholder 2026-11-04, issue #87 |
| v1.1.3 | 2026-11-01 | Twee logs: overzichten tonen alleen bootmutaties, technisch log onder een eigen menuoptie | Besluit stakeholder 2026-11-01, BLB-043, issue #38 |
| v1.1.2 | 2026-10-31 | CSP uit Traefik in plaats van Nginx | Besluit stakeholder 2026-10-31, issue #29 (ADR-013) |
| v1.1.1 | 2026-10-31 | Reden bij het alternatief SPA bijgewerkt (de API is niet meer alleen-lezen); logo uit de installatie | Besluiten stakeholder 2026-10-31 |
| v1.1.0 | 2026-10-31 | Tokens uit een aparte stylesheet `/huisstijl.css` in plaats van een `<style>`-blok met nonce | Slice 3 (issue #13); de CSP blijft ongewijzigd, beoordeeld door aegis |
| v1.0.0 | 2026-10-30 | Eerste versie | |
