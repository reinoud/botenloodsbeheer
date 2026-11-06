# ADR-009 Configuratie: in de applicatie of in de installatie

**Status:** Aanvaard, 2026-10-30 (API-schakelaar: besluit van de stakeholder, architectuur §9, besluit 5); herzien 2026-10-31 (logo en integratiecontainer)
**Datum:** 2026-10-30
**Versie:** v1.3.1
**Stories:** BLB-007, BLB-009, BLB-027, BLB-028, BLB-029

## Context

Elke vereniging draait een eigen installatie met eigen naam en logo (intake). Het logo staat sinds 2026-10-31 in de installatie; de naam stelt de beheerder in de applicatie in. De kleuren zijn vast sinds 2026-11-06 (ADR-002). De 12-factor-basis geldt: configuratie en geheimen uit de omgeving (overlay §6). Er zijn drie gelijke beheerders en geen systeembeheerrol. Wie de installatie neerzet, is dus vaak niet wie dagelijks beheert. De overlay (§4) legt per instelling de keuze bij foundation.

De vuistregel: wat de installatie technisch laat werken of een geheim is, staat in de omgeving. Wat een beheerder in het dagelijks werk wil aanpassen, staat in de applicatie, in de tabel `instelling`, en wijzigen geeft een logregel.

## Besluit

| Instelling | Waar | Standaard | Reden |
|------------|------|-----------|-------|
| `SECRET_KEY` | Omgeving | Geen; de applicatie start niet zonder | Geheim |
| `DATABASE_URL`, per dienst een eigen waarde en databaserol: `web` mag het log alleen lezen en aanvullen, `api` mag leden aanmaken en bijwerken, `worker` mag opschonen, `migrate` is eigenaar | Omgeving | Geen | Geheim, ADR-006 en ADR-012. Eén naam per dienst in plaats van een aparte `DATABASE_URL_TAKEN` (slice 1a) |
| `BASIS_URL` | Omgeving | Geen | Vast per installatie, altijd `https://` (besloten, §9 besluit 2); in QR-codes |
| `TOTP_SLEUTEL` | Omgeving | Geen; de applicatie start niet zonder | Geheim; versleutelt de TOTP-geheimen (ADR-001) |
| `API_INGESCHAKELD` | Omgeving | `true` | Besluit van de stakeholder: een installatiekeuze, standaard aan (2026-10-31); wijzigen vraagt een herstart van `api` en `web` (statuspagina). Uit betekent ook: geen import van leden |
| `KOPPELNET` | Omgeving (compose, `web`) | `10.203.0.0/24` | Subnet van het netwerk `koppeling` en standaardwhitelist van een nieuw robottoken (ADR-012) |
| `DB_API_WACHTWOORD` | Omgeving (`db`, `api`) | Geen | Geheim, voor de rol `botenloods_api` (ADR-012) |
| `WEBAUTHN_RP_ID` | Omgeving | Host uit `BASIS_URL` | Hoort bij de domeinnaam (ADR-001) |
| `DIENST` | Omgeving | `web` | `worker` of `api` in die containers; die hebben dan geen `SECRET_KEY` en `TOTP_SLEUTEL` nodig (slice 1b, ADR-012) |
| `APP_OMGEVING` | Omgeving | `productie` | Seed en debug alleen buiten productie |
| `PROXY_HOPS` | Omgeving | 1 | Bepaalt het vertrouwde clientadres (ADR-005) |
| `LEDENBRON`, `LEDENBRON_STUB_BESTAND` en inloggegevens van de bron | Omgeving van `integratie` | Leeg | Techniek en geheim (ADR-004); de applicatie kent ze niet |
| `API_URL`, `API_TOKEN_FILE`, `SYNC_TIJDSTIP` | Omgeving van `integratie` | `http://traefik:8081/api/v1` (instelbaar), `/run/secrets/api_token`, 03:00 | ADR-012, ADR-013 |
| `OPSCHOON_TIJDSTIP`, `TZ` | Omgeving (`OPSCHOON_TIJDSTIP` alleen `worker`) | 04:00, Europe/Amsterdam | Bedrijfsvoering van de installatie |
| `APP_VERSIE` | Buildargument van het image | `ontwikkeling` | Versie op de statuspagina (ADR-010) |
| `LOGO_BESTAND` | Omgeving (`web`), bestand in `./huisstijl` | `/huisstijl/logo.png`; zonder bestand alleen de naam | Besluit stakeholder 2026-10-31: logo in de installatie, wijzigen wordt niet gelogd (ADR-008) |
| `LOG_NIVEAU` | Omgeving | `INFO` | Techniek |
| `DOMEIN`, `INSTALLATIE`, `TRAEFIK_CERTRESOLVER` | Omgeving (compose-labels en netwerknamen) | Geen, `botenloods`, geen | `DOMEIN` gelijk aan de host uit `BASIS_URL`; `INSTALLATIE` uniek per host (ADR-013) |
| Naam van de vereniging | Applicatie | "Botenloods" | BLB-027 |
| Bootsoorten | Applicatie (tabel `bootsoort`, blok Bootsoorten op `/instellingen`) | Kajak, Canadese kano, surfski, C11, supboard | BLB-028 |

Vaste waarden in code, niet instelbaar: de bewaartermijn van 5 jaar, de maximale tokenduur van 3 jaar, de waarschuwing 31 dagen voor verlopen, de rechtenlijst van tokens, de uploadgrens. Dit zijn besluiten van de stakeholder of beveiligingsgrenzen, geen voorkeuren per vereniging. Wijzigen gaat via een release.

`config.py` leest de omgeving één keer bij het starten en stopt met een duidelijke foutmelding als een verplichte waarde ontbreekt of ongeldig is. `.env.example` bevat elke variabele met uitleg en zonder geheimen. Geheimen komen via een `.env`-bestand naast de compose (mode 0600) of via Docker secrets; de applicatie leest ook `<NAAM>_FILE` als pad naar een secret.

Instellingen in de applicatie leest de basistemplate per verzoek uit de database. Bij 3 beheerders en een paar honderd bezoekers per dag is caching niet nodig.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Alles in de omgeving | Naam of kleur wijzigen vraagt servertoegang en een herstart; er is geen systeembeheerrol. Voor het logo koos de stakeholder dit wel |
| Alles in de applicatie | Geheimen in de database en een bootstrapprobleem voor `SECRET_KEY` en de database zelf |
| API-schakelaar in de applicatie | Foundation raadde dit aan; de stakeholder koos de installatie |
| Configuratiebestand (YAML) in een volume | Derde plek naast omgeving en database |

## Gevolgen

- Een nieuwe installatie start met een neutrale naam (BLB-027). De naam is na de eerste inlog in te stellen; het logo zet wie de installatie draait in `./huisstijl`.
- Er komt geen scherm om de API aan of uit te zetten. Een wijziging van de schakelaar staat niet in het mutatielog; `api` meldt de stand bij het opstarten in de containerlog. Hetzelfde geldt voor het logo.
- De statuspagina toont of de API aan staat, de laatste import en wanneer de bootaantallen voor het laatst zijn opgehaald, nooit de waarden van geheimen (BLB-037, ADR-010). Welke bron de integratiecontainer gebruikt, weet de applicatie niet.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.4.0 | 2026-11-06 | Primaire en secundaire kleur vervallen; migratie 0015 verwijdert de rijen `kleur_primair` en `kleur_secundair` uit `instelling` | Besluit stakeholder 2026-11-06, issue #150 |
| v1.3.1 | 2026-11-03 | Bootsoorten beheerd op `/instellingen` | Bouw slice 11, issue #56 |
| v1.3.0 | 2026-11-02 | `APP_VERSIE`; `OPSCHOON_TIJDSTIP` alleen bij `worker`; `API_INGESCHAKELD` ook bij `web` | Bouw slice 9, issue #48 |
| v1.2.0 | 2026-10-31 | `DOMEIN`, `INSTALLATIE`, `TRAEFIK_CERTRESOLVER` toegevoegd; `API_URL` instelbaar | Besluit stakeholder 2026-10-31, issue #29 (ADR-013) |
| v1.1.0 | 2026-10-31 | `API_INGESCHAKELD` standaard `true`; `KOPPELNET`, `DB_API_WACHTWOORD`, `LOGO_BESTAND` toegevoegd; ledenbron en `SYNC_TIJDSTIP` naar de integratiecontainer; logo en terugschrijven niet meer in de applicatie | Besluiten stakeholder 2026-10-31, ADR-008, ADR-012 |
| v1.0.0 | 2026-10-30 | Eerste versie | |
