# ADR-015 Rollen en autorisatie: beheerder en kijker

**Status:** Besloten door Foundation, 2026-11-18; open vraag 1 wacht op de stakeholder
**Datum:** 2026-11-18
**Versie:** v1.0.0
**Stories:** BLB-050, BLB-051; issue #322

## Context

Elk account heeft nu dezelfde rechten; de 82 webroutes controleren alleen of iemand is ingelogd (`inloggen_vereist`). De stakeholder besloot op 2026-11-18 tot een tweede rol, de kijker, die een deel van de schermen ziet en niets wijzigt (intake).

## Besluit

**Rolmodel.** Elk account heeft één rol, `beheerder` of `kijker`, in de kolom `beheerder.rol`. `laad_beheerder` leest het account bij elk verzoek uit de database, dus ook de rol; die staat nooit in de sessiecookie. Een rolwijziging geldt bij het volgende verzoek, zonder dat sessies eindigen.

**Standaard geweigerd.** Aan het eind van `laad_beheerder` komt één controle: is de rol niet `beheerder` en staat het endpoint niet in de vaste lijst `KIJKER_TOEGESTAAN`, dan 403. Een onbekende rol valt ook onder de weigering. Een nieuwe route is voor een kijker dicht tot hij in de lijst staat. De lijst:

| Soort | Endpoints (blueprint `web`) |
|-------|-----------------------------|
| Inzien | `start`, `rekoverzicht`, `vrije_plaatsen`, `boten_overzicht`, `boot_detail`, `plaats_detail`, `zoeken`, `afbeelding`, `logo`, `openbare_plaats` |
| Eigen inlog | de vijftien endpoints van `app/web/inloggen.py`: inloggen, uitloggen, uitnodiging en profiel |

Alleen de POST-routes onder Eigen inlog mag een kijker doen; ze raken alleen zijn eigen sessie en inlogmethodes (open vraag 1). De blueprints `health` en `api` hebben geen sessie en vallen erbuiten.

Een test loopt `app.url_map` langs en doet voor elke regel van `web` buiten de lijst elke methode als kijker: 403. Een tweede test eist dat elk endpoint in de lijst bestaat. De E2E-proef stuurt een geldig CSRF-token mee.

**Tokens.** De tokenschermen staan niet in de lijst. Wordt een account kijker, dan trekt dezelfde transactie zijn persoonlijke tokens in, met `token.ingetrokken` per token. Terug naar beheerder brengt ze niet terug. De controle per aanroep (ADR-005) eist een eigenaar die actief en beheerder is (reden `eigenaar_inactief`); die vangt ook een token dat tijdens de rolwijziging nog ontstond. Robottokens blijven werken.

**Lidnummer en opzegdatum.** Een kijker ziet geen lidnummer, opzegdatum, datum lid sinds of oud-lidmelding (open vraag 2), en geen link naar een lid. `zoekopdracht.zoek` krijgt het argument `met_leden`; voor een kijker zoekt hij niet in `Lid.lidnummer` en geeft hij geen leden. `log.namen` toont "Lid <naam>" zonder nummer, en de link "Meer in het log" vervalt. Een test eist dat een herkenbaar lidnummer en opzegdatum op geen toegestaan scherm van een kijker staan, ook niet na zoeken op dat nummer.

**Laatste beheerder.** Gekozen is een vergrendeling, geen database-constraint. Rol wijzigen, blokkeren en verwijderen vergrendelen eerst alle actieve accounts (`FOR UPDATE`, `populate_existing=True`), zoals `_ander_account` nu doet. Onder dat slot is de actor een actieve beheerder en blijft na de wijziging minstens één actieve beheerder over. Bij twee gelijktijdige wijzigingen ziet de tweede de uitkomst van de eerste. De racetest laat twee beheerders tegelijk zichzelf en elkaar kijker maken en faalt met een mutant zonder slot.

**Gebruikers.** Alleen wat de gebruiker ziet, krijgt de nieuwe naam: menu, titel, teksten en URL. Model `Beheerder`, tabel `beheerder`, `domein/beheerders`, de logacties `beheerder.*`, de verwijzing `beheerder:<id>` en `flask beheerder` blijven. De routes `/beheerders...` worden `/gebruikers...`. `GET /beheerders` verwijst met 301 naar `/gebruikers`; de oude POST-routes vervallen. Het log toont `beheerder:<id>` als "Gebruiker <naam>".

**Uitnodigen en rol wijzigen.** Het uitnodigingsformulier vraagt de rol, zonder voorkeuze; de domeinfunctie krijgt de rol als verplicht argument. `flask beheerder uitnodigen` maakt een beheerder. Nieuw is `POST /gebruikers/<id>/rol`, met recente inlog (ADR-001), ook voor het eigen account.

**Log.** `beheerder.uitgenodigd` krijgt het veld `rol`. Nieuw is `beheerder.rol_gewijzigd` met `gebruikersnaam` en `rol: [oud, nieuw]`, in het technische log (`TECHNISCH`), alleen bij een echte wijziging.

## Migratie 0022

Bestand `0022_rol_per_account.py`, `down_revision = '0021'`, één head.

Upgrade:

1. Kolom `rol`, `VARCHAR(10) NOT NULL`, met server default `'beheerder'`: bestaande accounts worden beheerder.
2. Daarna vervalt de server default, en het model krijgt er geen: een vergeten rol geeft een fout.
3. Check `rol IN ('beheerder', 'kijker')`, naam `rol_geldig`, ook in `__table_args__`.
4. `GRANT SELECT (rol) ON beheerder TO botenloods_api` (tokencontrole). De tabelrechten van `botenloods_web` en `botenloods_taken` (migratie 0001) dekken de kolom al.

Downgrade: zonder kolom wordt elke kijker beheerder. Daarom blokkeert de downgrade eerst elke kijker (`actief = false`, sessieversie plus één), met per account een regel `beheerder.geblokkeerd` (actor systeem, naam `migratie`). Daarna vervallen recht, check en kolom. Na een nieuwe upgrade zijn dat geblokkeerde beheerders. De migratietest doet upgrade, downgrade en upgrade met een kijker.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Decorator per route | Wie hem vergeet, opent de route; de centrale controle sluit standaard |
| Tabel met rechten per rol | Twee vaste rollen passen in één kolom |
| Constraint-trigger voor de laatste beheerder | Een CHECK kijkt niet over rijen; een trigger is PL/pgSQL voor een handvol accounts, het slot bestaat al |
| Model en tabel hernoemen | Raakt migraties, opgeslagen logregels (ADR-006) en tests |

## Gevolgen

- ADR-001, ADR-002, ADR-005, ADR-006 en ADR-010 zijn bijgewerkt.
- Restrisico: een verzoek dat al loopt tijdens een rolwijziging, eindigt nog met de oude rol, net als bij blokkeren.

## Open vragen

| # | Vraag | Blokkerend | Aanbeveling |
|---|-------|------------|-------------|
| 1 | Mag een kijker in Profiel zijn eigen inlogmethodes toevoegen en intrekken? Backlog vraag 32; de intake ("weigert elke mutatie") sluit het strikt uit. | Ja, voor de profielroutes | Ja: geen gegevens van de loods; anders herstelt een beheerder bij elk verloren toestel |
| 2 | Ziet een kijker dat een eigenaar oud-lid is? | Nee | Nee (zo besloten): de melding volgt uit de opzegdatum |

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.0.0 | 2026-11-18 | Eerste versie | Besluiten stakeholder 2026-11-18, issue #322 |
