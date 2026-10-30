# ADR-011 Keuze van bibliotheken

**Status:** Aanvaard, 2026-10-30 (aangepast voor besluit 1, inlogmethode)
**Datum:** 2026-10-30
**Stories:** alle; vooral BLB-017, BLB-021, BLB-022, BLB-034

## Context

De stack staat vast: Python, Flask, Gunicorn, Nginx en PostgreSQL. Binnen die stack zijn keuzes nodig voor de database-laag en migraties, formulieren en CSRF, inloggen (passkeys, wachtwoordhash, TOTP), afbeeldingen, Excel, QR-codes, het printen van kaartjes, de OpenAPI-beschrijving en de tests. Elke afhankelijkheid is onderhoud en een mogelijk lek in de toeleveringsketen. De regel is daarom: een bibliotheek alleen als die een echt probleem oplost dat niet in een paar regels code te doen is, en dan een breed gebruikte, onderhouden bibliotheek.

## Besluit

| Doel | Keuze | Reden |
|------|-------|-------|
| Webframework en server | Flask, Gunicorn | Vast kader |
| Database-laag | SQLAlchemy 2 met Flask-SQLAlchemy, driver psycopg 3 | Standaard bij Flask; ondersteunt `cidr`, `bytea`, `jsonb`, arrays en `SELECT ... FOR UPDATE` |
| Migraties | Alembic | Standaard bij SQLAlchemy; autogenerate als begin, migraties altijd met de hand nagelopen; elke migratie met een werkende downgrade |
| Formulieren en CSRF | Flask-WTF | CSRF-bescherming op elk formulier en validatie op vorm in één bibliotheek |
| Passkeys | `webauthn` (py_webauthn) | Onderhouden implementatie van registratie en verificatie; zelf bouwen van WebAuthn-verificatie is foutgevoelig |
| Wachtwoordhash | `argon2-cffi` | Argon2id met veilige standaardparameters en herhashen; zelf een hash kiezen of afstellen is foutgevoelig (ADR-001) |
| TOTP | `pyotp` | Kleine, breed gebruikte RFC 6238-implementatie met vergelijking in constante tijd; de QR-code komt van segno |
| Versleuteling TOTP-geheim | `cryptography` (Fernet) | Komt al mee als afhankelijkheid van `webauthn`; geen eigen cryptografie |
| Afbeeldingen | Pillow | Herkennen, verkleinen, metadata verwijderen (ADR-008) |
| Excel-export | openpyxl | Schrijft `.xlsx` zonder Office; één werkblad met kolombreedtes en een kopregel is genoeg |
| QR-codes | segno | Pure Python zonder afhankelijkheden, levert SVG die scherp print en direct in HTML past |
| Kaartjes printen | HTML met print-CSS, print via de browser | Geen pdf-bibliotheek nodig; de browser maakt een pdf als de beheerder dat wil |
| OpenAPI | Handgeschreven `openapi.yaml`, gecontroleerd met openapi-spec-validator | Acht leesendpoints; een generator kost meer dan hij scheelt |
| Tests | pytest, Playwright voor Python | Unit, integratie en E2E in één taal |
| Lint en opmaak | ruff | Eén snelle tool |
| Pakketbeheer | uv met lockbestand | Vaste versies en reproduceerbare builds |

**Kaartjes.** De printpagina toont per plaats een kaartje met logo, plaatscode, naam van de eigenaar (of "vrij", of de naam van de vereniging bij een clubplaats) en de QR-code als inline SVG. Print-CSS zet een vast aantal kaartjes per A4 met snijlijnen en voorkomt dat een kaartje over twee pagina's valt. De beheerder kiest één, meerdere of alle plaatsen met selectievakjes of per rek.

**OpenAPI.** De beschrijving staat in `app/api/openapi.yaml` en is te zien via `/api/v1/openapi.json` en een eenvoudige HTML-pagina die de endpoints uit de beschrijving opsomt (BLB-034). Een test vergelijkt de routes van de blueprint met de paden in de beschrijving en controleert de voorbeeldantwoorden tegen de schema's. Een route zonder beschrijving laat de test falen.

## Alternatieven

| Doel | Afgewezen | Waarom |
|------|-----------|--------|
| Migraties | Flask-Migrate | Dunne laag over Alembic die bij één database niets toevoegt |
| Excel | XlsxWriter, pandas | XlsxWriter is ook goed; openpyxl kan later ook lezen, wat de spreadsheetimport (later) helpt; pandas is veel te zwaar |
| QR | qrcode | Heeft Pillow nodig voor bitmaps; segno levert SVG zonder extra afhankelijkheid |
| Printen | WeasyPrint, ReportLab | Systeembibliotheken (Pango, Cairo) in het image of een eigen opmaaktaal; de browser print al goed |
| OpenAPI | flask-smorest, apispec, spectree | Schema-laag en extra afhankelijkheden voor een handvol leesroutes |
| Formulieren | Alleen eigen validatie | CSRF zelf bouwen is een bekende bron van fouten |

## Gevolgen

- Het image heeft geen systeembibliotheken nodig buiten wat Pillow en psycopg als wheel meenemen; `python:3.14-slim` volstaat.
- Kaartjes zien er per browser iets anders uit. Forge test de printpagina in Chromium en Firefox.
- Aegis scant de afhankelijkheden na elke mijlpaal (overlay §7). Forge houdt het lockbestand bij.
- Een nieuwe afhankelijkheid buiten deze lijst vraagt een korte notitie van forge aan foundation met reden en alternatief.
