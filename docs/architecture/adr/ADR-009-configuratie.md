# ADR-009 Configuratie: in de applicatie of in de installatie

**Status:** Besloten door Foundation, behalve de API-schakelaar (architectuur §9, besluit 5)
**Datum:** 2026-10-30
**Stories:** BLB-007, BLB-009, BLB-027, BLB-028, BLB-029

## Context

Elke vereniging draait een eigen installatie met eigen naam, kleuren en logo (intake). De 12-factor-basis geldt: configuratie en geheimen uit de omgeving (overlay §6). Er zijn drie gelijke beheerders en geen systeembeheerrol. Wie de installatie neerzet, is dus vaak niet wie dagelijks beheert. De overlay (§4) legt per instelling de keuze bij foundation.

De vuistregel: wat de installatie technisch laat werken of een geheim is, staat in de omgeving. Wat een beheerder in het dagelijks werk wil aanpassen, staat in de applicatie, in de tabel `instelling`, en wijzigen geeft een logregel.

## Besluit

| Instelling | Waar | Standaard | Reden |
|------------|------|-----------|-------|
| `SECRET_KEY` | Omgeving | Geen; de applicatie start niet zonder | Geheim |
| `DATABASE_URL` (web, alleen lezen en toevoegen op het log) | Omgeving | Geen | Geheim, ADR-006 |
| `DATABASE_URL_TAKEN` (worker, mag opschonen) | Omgeving | Geen | Geheim, ADR-006 |
| `BASIS_URL` | Omgeving | Geen | Vast per installatie; in QR-codes |
| `WEBAUTHN_RP_ID` | Omgeving | Host uit `BASIS_URL` | Hoort bij de domeinnaam (ADR-001) |
| `APP_OMGEVING` | Omgeving | `productie` | Seed en debug alleen buiten productie |
| `PROXY_HOPS` | Omgeving | 1 | Bepaalt het vertrouwde clientadres (ADR-005) |
| `LEDENBRON` en inloggegevens van de bron | Omgeving | Leeg | Techniek en geheim (ADR-004) |
| `LEDENBRON_STUB_BESTAND` | Omgeving | Fixture | Alleen voor de stub |
| `SYNC_TIJDSTIP`, `OPSCHOON_TIJDSTIP`, `TZ` | Omgeving | 03:00, 04:00, Europe/Amsterdam | Bedrijfsvoering van de installatie |
| `LOG_NIVEAU` | Omgeving | `INFO` | Techniek |
| Naam van de vereniging | Applicatie | "Botenloods" | BLB-027 |
| Primaire en secundaire kleur | Applicatie | Neutraal grijs en blauw | BLB-027, design tokens (ADR-002) |
| Logo | Applicatie | Geen; alleen de naam | BLB-027, ADR-008 |
| Bootsoorten | Applicatie (tabel `bootsoort`) | Kajak, Canadese kano, surfski, C11, supboard | BLB-028 |
| API aan of uit | Applicatie | Uit | Besluit 5 voor de stakeholder |
| Terugschrijven aan of uit | Applicatie, vergrendeld | Uit | BLB-009; aanzetten geeft een melding (ADR-004) |

Vaste waarden in code, niet instelbaar: de bewaartermijn van 5 jaar, de maximale tokenduur van 3 jaar, de waarschuwing 31 dagen voor verlopen, de rechtenlijst van tokens, de uploadgrens. Dit zijn besluiten van de stakeholder of beveiligingsgrenzen, geen voorkeuren per vereniging. Wijzigen gaat via een release.

`config.py` leest de omgeving één keer bij het starten en stopt met een duidelijke foutmelding als een verplichte waarde ontbreekt of ongeldig is. `.env.example` bevat elke variabele met uitleg en zonder geheimen. Geheimen komen via een `.env`-bestand naast de compose (mode 0600) of via Docker secrets; de applicatie leest ook `<NAAM>_FILE` als pad naar een secret.

Instellingen in de applicatie leest de basistemplate per verzoek uit de database. Bij 3 beheerders en een paar honderd bezoekers per dag is caching niet nodig.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Alles in de omgeving | Naam, kleur of logo wijzigen vraagt servertoegang en een herstart; er is geen systeembeheerrol |
| Alles in de applicatie | Geheimen in de database en een bootstrapprobleem voor `SECRET_KEY` en de database zelf |
| API-schakelaar in de omgeving | Zie besluit 5: dan is servertoegang nodig voor een gewone beheerkeuze. Wel te verdedigen als de stakeholder de API als installatiekeuze ziet |
| Configuratiebestand (YAML) in een volume | Derde plek naast omgeving en database |

## Gevolgen

- Een nieuwe installatie start met neutrale naam en stijl (BLB-027) en heeft na de eerste inlog de eigen huisstijl.
- Kiest de stakeholder bij besluit 5 voor de omgeving, dan verhuist één regel uit deze tabel en vervalt het scherm voor die schakelaar.
- De statuspagina toont welke ledenbron actief is en of API en terugschrijven aan staan, nooit de waarden van geheimen (BLB-037).
