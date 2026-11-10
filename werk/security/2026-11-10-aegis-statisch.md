# Statische securityronde vóór release v1.0.0

**Datum:** 2026-11-10
**Agent:** aegis
**Commit:** 6ee8ee9 (main), vergeleken met d2c34b7 van de vorige ronde
**Normen:** ADR-001, ADR-004, ADR-005, ADR-008, ADR-012, ADR-013, ADR-014; overlay §6, §7 en §8

## Oordeel

Goed genoeg, binnen de beoordeelde scope. Ik vond geen bevinding met ernst hoog of middel, dus niets blokkeert de release. Er is één bevinding met ernst laag (AEG-08, #230) en er zijn twee adviespunten. De afhankelijkheden en beide images hebben geen bekende kwetsbaarheid met een beschikbare oplossing. De punten AEG-01 tot en met AEG-06 uit de vorige ronde zijn opgelost; AEG-04 bewust gedeeltelijk (zie onder).

## Scope

Beoordeeld: de wijzigingen sinds d2c34b7 in `app/`, `integratie/`, `migrations/`, `docker/`, de compose-bestanden (ook het voorbeeld in `documentatie/beheer/voorbeelden/traefik/`) en `.github/`. Het zwaartepunt lag op externe invoer: de bron e-boekhouden en het terugschrijven (`integratie/koppeling/`), de CSV-imports van rekindeling en bezetting, de uploads van foto en logo, en de tokens en leesaanroepen van de API.

Verder:

- `uv.lock`, `integratie/requirements.txt` en `tests/e2e/requirements.txt` met trivy fs 0.76.1 (ook dev-afhankelijkheden) en pip-audit;
- de images `proef/aegis-app:6ee8ee9` en `proef/aegis-integratie:6ee8ee9`, gebouwd als linux/amd64 uit een export van 6ee8ee9, gescand met de Trivy-regel uit `images.yml` en volledig;
- bandit op `app/`, `integratie/koppeling/` en `migrations/`;
- tabelrechten, rollen en policies met leesquery's in de gedeelde database (stack `botenloods`, migratie 0020).

Niet beoordeeld: templates per regel (wel gezocht naar `|safe` en onveilige JavaScript), CSS, fonts en plaatjes, de testcode, de documentatie buiten het Traefik-voorbeeld, en de bedrijfslogica van de imports buiten de grenzen en validatie. Geen live proeven, geen unitsuite en geen `draai.sh`; de DAST doet probe. De echte dienst van e-boekhouden heb ik niet aangeroepen.

## Bevindingen

| Code | Ernst | Bestand:regel | Kort | Issue |
|------|-------|---------------|------|-------|
| AEG-08 | laag | `documentatie/beheer/voorbeelden/traefik/compose.yml:7,16`, `.github/dependabot.yml:41-46` | Voorbeeld-Traefik zonder digest, buiten Dependabot en zonder hardening | #230 |
| AEG-09 | advies | `docker-compose.yml:217-219` | Inloggegevens van e-boekhouden als omgevingsvariabele | nee |
| AEG-10 | advies | `pyproject.toml:30-33` | `exclude-newer` staat op 2026-10-21 | nee |

### AEG-08: voorbeeld-Traefik zonder digest en hardening

Het voorbeeld voor een gedeelde Traefik haalt `traefik:v3.7.17` en de socketproxy op met alleen een tag. De afspraak uit #25 (elk image op een digest) geldt in de eigen compose-bestanden wel. Dependabot kijkt voor `docker-compose` alleen in `/`, dus dit bestand krijgt geen updates. Beide diensten missen `read_only`, `cap_drop` en `no-new-privileges`.

Een vereniging neemt dit voorbeeld over voor de Traefik die op internet staat. De ernst blijft laag: de socketproxy laat alleen het lezen van containers toe en het netwerk `socket` is intern.

**Actie.** Digest op beide images, de map in `dependabot.yml`, en de drie beperkingen, met `cap_add: [NET_BIND_SERVICE]` voor Traefik. De acceptatiecriteria staan in #230.

### AEG-09: inloggegevens van e-boekhouden in de omgeving

`EBOEKHOUDEN_CODE1` en `EBOEKHOUDEN_CODE2` gaan als omgevingsvariabele naar de integratiecontainer. Ze zijn zichtbaar met `docker inspect`, en met `BOOTAANTALLEN_SCHRIJVEN=aan` geven ze schrijfrecht in de administratie van de vereniging. Overlay §8 staat de omgeving toe, en `SECRET_KEY` en de databasewachtwoorden gaan op dezelfde manier. Het API-token gaat al als secretbestand. Advies: lees de codes op dezelfde manier uit een secret, en noem in `integratiecontainer.md` dat de vereniging in e-boekhouden een aparte API-gebruiker aanmaakt.

### AEG-10: exclude-newer loopt achter

`exclude-newer` staat op 2026-10-21, met een uitzondering voor pyasn1 tot 2026-10-28. De scans zijn nu schoon, dus er wacht geen oplossing. Een oplossing die na 21 oktober verschijnt, komt er pas in na een handmatige ophoging, en Dependabot stelt binnen die grens niets voor (#59). Met een cooldown van 14 dagen kan de datum vandaag naar 2026-10-27; de uitzondering voor pyasn1 vervalt dan zodra 2026-10-28 bereikt is. Advies: hoog de datum op bij elke mijlpaal.

## Afhankelijkheden en images

Trivy fs en pip-audit vinden niets in de drie lijsten. Pillow staat op 13.0.0, pyasn1 op 0.6.5 en pytest op 9.0.3. De integratiecontainer installeert met `--require-hashes --only-binary :all:`.

Beide images slagen voor de Trivy-regel uit `images.yml` (exit 0). Er zijn geen meldingen in Python-pakketten en geen geheimen. Meldingen zonder oplossing, alle in Debian 13.7:

| Image | High | Medium | Low | Unknown | Met oplossing |
|-------|------|--------|-----|---------|---------------|
| app | 103 | 96 | 86 | 15 | 0 |
| integratie | 47 | 74 | 65 | 15 | 0 |

Het verschil komt vooral van `libpq5` en wat dat meebrengt (#86).

## Vorige ronde

- **AEG-01** opgelost: Pillow 13.0.0 en `Image.open(..., formats=OPENEN)` in `app/domein/afbeeldingen.py:32`.
- **AEG-02** opgelost: trivy vóór de push in `images.yml`, Dependabot voor uv, pip, actions, docker en compose.
- **AEG-03** opgelost: geen meldingen meer; psycopg gebruikt nu `libpq5` uit Debian.
- **AEG-04** gedeeltelijk, bewust: migratie 0010 (#60) haalt de rechten op `beheerder`, `passkey` en `uitnodiging` weg. INSERT en UPDATE op indeling en boten blijven, omdat `flask seed` als `botenloods_taken` draait. Seed weigert in productie (`app/seed.py:65`). Dat aanvaard ik.
- **AEG-05** opgelost: alle actions staan op een commit-SHA.
- **AEG-06** opgelost: `cap_drop: [ALL]` in `x-app`.
- **AEG-07** ongewijzigd adviespunt.
- **#12** is opgelost: blokkeren, deblokkeren en verwijderen vragen een recente inlog (`app/web/beheer.py:518`). **#20** valt onder de waiver in #103.

## Wat klopt

Kort, als tegenbewijs:

- De bron e-boekhouden gebruikt een vaste https-URL en een WSDL uit het image, zet het logniveau van zeep op WARNING (geen inloggegevens in het log) en zet een fout om naar een reden uit de vaste lijst. Alleen lidnummer, naam en twee datums gaan naar de API; daar valideert `leden.valideer` type, lengte, datum en NUL-teken.
- De container volgt geen redirect met het token en leest hooguit 256 kB per antwoord van de API.
- De CSV-imports begrenzen grootte (256 kB), regels (2000) en meldingen (50), weigeren stuurtekens en NUL, en beschermen formules in de export. Een melding met inhoud uit het bestand gaat niet in de sessiecookie. De keuzes in het koppelscherm worden tegen de regels, actieve leden en toegestane soorten gecontroleerd.
- Upload, import en bevestigen vragen een recente inlog. Het logo is een PNG uit `afbeeldingen.verwerk` en `/logo/<kenmerk>` geeft alleen een afbeelding met soort `logo`.
- Het recht `persoonsgegevens` is weg (migratie 0018); lid sinds en opzegdatum gaan mee met `leden:lezen`, volgens het besluit in ADR-012 v1.9.0.
- Het CLI-recht `leden:importeren` vergelijkt nu op de CLI-actor zelf, niet op de soort (#118).
- RLS op `taakrun` beperkt `botenloods_api` tot de taken `ledenimport` en `bootaantallen`. Geen enkele app-rol is superuser of heeft BYPASSRLS. `botenloods_web` kan `logregel` niet wijzigen of verwijderen.
- Het enige `|safe` staat op de SVG van segno; bandit vindt alleen `random` in de seed.
- De buffering van 25 MB in het geheugen van Traefik zonder inlog is in ADR-013 aanvaard; ik heb dat niet opnieuw beoordeeld.

## Open vragen

Geen blokkerende. Niet blokkerend: wil de stakeholder AEG-09 als taak, of blijft de omgeving voor alle geheimen de afspraak?
