# Wijzigingen

Per versie de wijzigingen, gelijk aan de releasenotes op GitHub (https://github.com/reinoud/botenloodsbeheer/releases). De nieuwste versie staat bovenaan.

## 1.3.0 (2026-11-17)

Versie met oud-leden als eigenaar en een SBOM per image (milestone "Oud-leden als eigenaar en SBOM"). Neemt ook twee zichtbare wijzigingen uit milestone 7 mee.

**Images** (linux/amd64), gescand met trivy vóór de push:
- `ghcr.io/reinoud/botenloods-app:1.3.0`
- `ghcr.io/reinoud/botenloods-integratie:1.3.0`

Ook beschikbaar onder de tags `1.3` en `latest`. Bij de release staat per image een SBOM in CycloneDX-formaat: `botenloods-app-1.3.0.cdx.json` en `botenloods-integratie-1.3.0.cdx.json` (#297).

**Nieuw sinds 1.2.0**
- Een boot van een oud-lid is vast te leggen en krijgt een plaats, maar geen clubplaats en geen plek op de wachtlijst. Een oud-lid van wie de opzegdatum hooguit 5 jaar geleden is, staat met de tag oud-lid in de keuze Eigenaar en op Leden. Daarbuiten is het oud-lid niet te kiezen en krijgt zijn boot geen nieuwe plaats; verplaatsen mag wel (#298).
- De ledenimport neemt oud-leden op tot 5 jaar na hun opzegdatum. Voor oud-leden schrijft de applicatie geen bootaantal naar e-boekhouden (#298).
- Een lid kiezen gaat met een zoekveld en een tussenstap, bij Nieuwe boot, Boot wijzigen, Boten zonder eigenaar en de bezettingsimport, in plaats van een lijst met ruim 200 namen (#295).
- Per image een SBOM als bijlage bij de release (#297).

**Gewijzigd**
- De veiligheidsgrens van de ledenimport telt opgezegde en ongeldige records niet meer mee (#307).
- De bezettingsimport en het koppelscherm blijven een oud-lid weigeren (#298).
- Op de pagina van een plaats en in de zoekresultaten staat de tag oud-lid achter de naam (#268, #298).
- De knop Zoeken in de kop toont op een smal scherm een vergrootglas (#275).
- Testonderhoud: opruimen van E2E-gegevens en een slottest op vergrendelen (#278, #283, #300).

**Bijwerken vanaf 1.2.0** (zie `documentatie/beheer/bijwerken.md`). Er is geen migratie; `docker-compose.yml` en `.env` zijn niet gewijzigd. Let op bij de eerste ledenimport na het bijwerken:
- Oud-leden met een opzegdatum van hooguit 5 jaar geleden komen erbij, ook oud-leden zonder boot die eerder zijn verwijderd. Na 5 jaar ruimt de opschoning ze weer op.
- Levert e-boekhouden `lid_sinds` of de opzegdatum niet als JJJJ-MM-DD, dan stopt de import met een 409 en blijven de leden ongewijzigd (#307).

## 1.2.0 (2026-11-15)

Versie met schermverbeteringen en een leesbaar log na 1.1.0 (milestone "Schermen en log na v1.1.0").

**Images** (linux/amd64), gescand met trivy vóór de push:
- `ghcr.io/reinoud/botenloods-app:1.2.0`
- `ghcr.io/reinoud/botenloods-integratie:1.2.0`

Ook beschikbaar onder de tags `1.2` en `latest`.

**Nieuw sinds 1.1.0**
- Het log toont leesbare tekst: "plaats toegewezen" en "Plaats F/4/1, Boot Zwaluw 7, Lid Anna de Boer (1184)" in plaats van de interne namen. Het technische log blijft de opgeslagen namen tonen (#174).
- Het zoekformulier in de kop en de zoekformulieren op de schermen hebben elk een eigen naam voor een schermlezer (#267).

**Gewijzigd**
- Op een telefoon (360 px) loopt het scherm Boot niet meer buiten de breedte (#270, #169).
- De tokentabel stapelt als kaart onder 67rem, zodat Intrekken zonder scrollen in beeld blijft (#192).
- Bezettingsimport: na Regel overslaan staan de soorten van de plaats weer in de lijst (#218). Een onverwachte databasefout bij het uploaden zet geen inhoud uit het bestand meer in de log (#167).
- De CSV-download van de rekindeling heeft `X-Content-Type-Options: nosniff`. De standaardbootsoort per verdieping gaat niet mee in de CSV; een rek uit een import heeft geen standaard (#164).
- Extra tests op volgorde, migratieheads en de uploadgrenzen van 10 en 25 MB via Traefik (#153, #149, #161, #209).

**Bijwerken vanaf 1.1.0** (zie `documentatie/beheer/bijwerken.md`). Er is geen migratie; `docker-compose.yml` en `.env` zijn niet gewijzigd.

## 1.1.0 (2026-11-14)

Featureversie na 1.0.2 (milestone "Features na v1.0.2").

**Images** (linux/amd64), gescand met trivy vóór de push:
- `ghcr.io/reinoud/botenloods-app:1.1.0`
- `ghcr.io/reinoud/botenloods-integratie:1.1.0`

Ook beschikbaar onder de tags `1.1` en `latest`.

**Nieuw sinds 1.0.2**
- Zoeken naar een plaats, boot of eigenaar vanuit de kop van elk beheerscherm (#154).
- Een boot verplaatsen vanaf het scherm Boot, in één handeling (#206).
- Een QR-code bij de uitnodigingslink en bij "Toegang hersteld" (#159).
- Het menu staat in vier groepen; Indeling en Import/export zijn aparte pagina's (#262).

**Gewijzigd**
- e-boekhouden: een Def2 met een hoofdletter of spaties, zoals `Actief_gewoon`, telt nu als lid (#226).
- De images worden bij een release zonder buildcache gebouwd, zodat ze de beveiligingsupdates van Debian bevatten, zoals libpq5 17.12 (#272).
- pytest 9.2.0 in integratie en E2E (#258); docker-socket-proxy v0.5.0 in het voorbeeld van Traefik (#249).

**Bijwerken vanaf 1.0.2** (zie `documentatie/beheer/bijwerken.md`). Er is geen migratie; `docker-compose.yml` en `.env` zijn niet gewijzigd.

## 1.0.2 (2026-11-12)

Onderhoudsversie na 1.0.1 (milestone "Restpunten na v1.0.1").

**Images** (linux/amd64), gescand met trivy vóór de push:
- `ghcr.io/reinoud/botenloods-app:1.0.2`
- `ghcr.io/reinoud/botenloods-integratie:1.0.2`

Ook beschikbaar onder de tags `1.0` en `latest`.

**Gewijzigd sinds 1.0.1**
- Een robottoken weigert een whitelist breder dan /8 (IPv4) of /32 (IPv6), zoals `0.0.0.0/0` (#243).
- Een boot van een oud-lid op de wachtlijst kan van de wachtlijst af (#176).
- De melding bij "eigenaar onbekend" leest niet meer als een andere eigenaar (#240).
- Een geweigerde foto of nieuwe boot houdt het blok open, met de melding erbij (#208).
- Een lid met de naam "clubboot" komt door export en import van de bezetting (#214).
- Dependabot vindt beide compose-bestanden (#230).

**Bijwerken vanaf 1.0.1** (zie `documentatie/beheer/bijwerken.md`). Er is geen migratie; `docker-compose.yml` en `.env` zijn niet gewijzigd. De grens op de whitelist geldt bij het maken van een token: een bestaand token met een bredere reeks blijft werken tot het verloopt of wordt ingetrokken.

**Bekend, ernst laag:** #226 (Def2 met een hoofdletter in e-boekhouden).

## 1.0.1 (2026-11-11)

Onderhoudsversie na 1.0.0 (milestone "Onderhoud na v1.0.0").

**Images** (linux/amd64), gescand met trivy vóór de push:
- `ghcr.io/reinoud/botenloods-app:1.0.1`
- `ghcr.io/reinoud/botenloods-integratie:1.0.1`

Ook beschikbaar onder de tags `1.0` en `latest`.

**Gewijzigd sinds 1.0.0**
- Zoeken in leden en boten maakt geen onderscheid meer in accenten: "Bertrand" vindt ook "Bértrand" (#232).
- Een boot met een eigenaar kan weer op "eigenaar onbekend" (#233).
- Op het plaatsscherm linkt de naam van de eigenaar naar het lid (#234).
- Een whitelist van een token met een IPv6-adres met zone-index geeft een melding in plaats van een fout 500 (#231).
- Het voorbeeld voor Traefik gebruikt images op digest, staat onder Dependabot en draait met minder rechten (#230).
- Afhankelijkheden bijgewerkt binnen de wachttijd van 14 dagen (#235).
- Drie wisselvallige E2E-tests hersteld (#172, #217, #213).

**Bijwerken vanaf 1.0.0** (zie `documentatie/beheer/bijwerken.md`). Maak eerst een back-up van de database.
- Migratie 0021 zet de PostgreSQL-extensie `unaccent` aan. Die extensie is vertrouwd; de eigenaar van de database mag haar aanmaken.
- `docker-compose.yml` en `.env` zijn niet gewijzigd. Wie het voorbeeld voor Traefik gebruikt, haalt `documentatie/beheer/voorbeelden/traefik/compose.yml` opnieuw op bij de tag `v1.0.1`.

**Bekend, ernst laag:** #226 (Def2 met een hoofdletter in e-boekhouden).

## 1.0.0 (2026-11-10)

Eerste volledige versie van botenloodsbeheer, na een securityronde (statische analyse door aegis en DAST door probe; verslagen in `werk/security/2026-11-10-*`). Er is geen bevinding met ernst hoog of middel.

**Images** (linux/amd64), gescand met trivy vóór de push:
- `ghcr.io/reinoud/botenloods-app:1.0.0`
- `ghcr.io/reinoud/botenloods-integratie:1.0.0`

Ook beschikbaar onder de tags `1.0` en `latest`.

**Nieuw en gewijzigd sinds 0.4.1**
- Een boot heeft een eigenaar, is clubboot of heeft een onbekende eigenaar. Er is een scherm Boten zonder eigenaar, en de API levert clubboten (#204, #207, #212).
- Een clubboot mag ook op een gewone plaats liggen (#205).
- Bezettingsimport: bij een onbekende bootsoort kies je de soort (#202).
- De ledenimport neemt geen nieuw lid op dat al opgezegd is. Bij e-boekhouden wordt een relatie op "opgezegd" zonder opzegdatum overgeslagen (#203, #221).
- Een foto of logo boven 10 MB geeft een melding op het formulier (#190).
- Een lange tokennaam breekt af; het keuzeteken bij Soort is rond (#191).
- uv in de build naar 0.13.5, trivy naar 0.76.1 (#196, #183).

**Bijwerken vanaf 0.4.1** (zie `documentatie/beheer/bijwerken.md`). Maak eerst een back-up van de database.
- Migratie 0019 zet elke bestaande boot zonder lid op clubboot.
- Migratie 0020 verwijdert oud-leden zonder boot (opzegdatum op of vóór de dag van de migratie). De downgrade zet ze niet terug.
- `docker-compose.yml` is gewijzigd: de grens voor foto's en logo in Traefik gaat van 10 naar 25 MB, zodat de applicatie de melding kan geven. Haal het bestand opnieuw op bij de tag `v1.0.0`.
- Geen nieuwe variabelen in `.env`.

**Bekend, ernst laag:** #226 (Def2 met een hoofdletter in e-boekhouden), #230 (voorbeeld van Traefik zonder digest), #231 (IPv6 met zone-index in de whitelist van een token geeft een fout 500).

## 0.4.1 (2026-11-09)

Vierde release van botenloodsbeheer, gelijk aan 0.4.0 plus de zlib-fix (0.4.0 heeft geen images): de rest van het nieuwe ontwerp, de koppeling met e-boekhouden, het logo uploaden in de applicatie en geen contactgegevens van leden meer.

**Images** (linux/amd64), gescand met trivy vóór de push:
- `ghcr.io/reinoud/botenloods-app:0.4.1`
- `ghcr.io/reinoud/botenloods-integratie:0.4.1`

Ook beschikbaar onder de tags `0.4` en `latest`.

**Nieuw en gewijzigd**
- Nieuw ontwerp, blokken 2 tot en met 4: openbare plaatspagina, scherm met vrije plaatsen, lijsten met zoeken en filters, log per dag, detail van boot en lid, en toegang en beheer met de passkey eerst (#150 deel 2, #181).
- Integratiecontainer met de ledenbron e-boekhouden; terugschrijven van bootaantallen staat standaard uit tot na de live proef (#178).
- Logo uploaden en verwijderen op Instellingen, zonder herstart; het logo in de installatie vervalt (#186).
- Adres, telefoon en e-mail van leden en het tokenrecht `persoonsgegevens` zijn weg (#180).
- De lidpagina toont geen lijst "Aantal boten per bootsoort" meer (#179).
- Na een mislukte poging staat het wachtwoordblok op Uitnodiging en Profiel open (#188).
- zlib1g in beide images bijgewerkt (CVE-2026-85091, CVE-2026-76844); Trivy stopte daarop de release 0.4.0 (#199).

**Bijwerken vanaf 0.3.0** (zie `documentatie/beheer/bijwerken.md`). Maak eerst een back-up van de database.
- Migratie 0017 zet het logo in de database. Upload een bestaand logo één keer op Instellingen. De downgrade verwijdert een geüpload logo.
- Migratie 0018 verwijdert de contactgegevens van leden en het recht `persoonsgegevens`; een actief token met alleen dat recht wordt ingetrokken. De downgrade zet de gegevens niet terug.
- `docker-compose.yml` is gewijzigd (geen koppeling van `./huisstijl` meer, een router voor `/instellingen/logo`, variabelen voor e-boekhouden): haal hem opnieuw op bij de tag `v0.4.1`.
- Nieuw in `.env`, alleen bij `LEDENBRON=eboekhouden`: `EBOEKHOUDEN_USERNAME`, `EBOEKHOUDEN_CODE1`, `EBOEKHOUDEN_CODE2` en `BOOTAANTALLEN_SCHRIJVEN`. `LOGO_BESTAND` vervalt.

## 0.4.0 (2026-11-09)

**Deze release heeft geen images.** Trivy stopte de workflow op twee meldingen HIGH in zlib1g (#199). Gebruik v0.4.1: dezelfde inhoud plus de fix.

Vierde release van botenloodsbeheer: de rest van het nieuwe ontwerp, de koppeling met e-boekhouden, het logo uploaden in de applicatie en geen contactgegevens van leden meer.

**Images** (linux/amd64), gescand met trivy vóór de push:
- `ghcr.io/reinoud/botenloods-app:0.4.0`
- `ghcr.io/reinoud/botenloods-integratie:0.4.0`

Ook beschikbaar onder de tags `0.4` en `latest`.

**Nieuw en gewijzigd**
- Nieuw ontwerp, blokken 2 tot en met 4: openbare plaatspagina, scherm met vrije plaatsen, lijsten met zoeken en filters, log per dag, detail van boot en lid, en toegang en beheer met de passkey eerst (#150 deel 2, #181).
- Integratiecontainer met de ledenbron e-boekhouden; terugschrijven van bootaantallen staat standaard uit tot na de live proef (#178).
- Logo uploaden en verwijderen op Instellingen, zonder herstart; het logo in de installatie vervalt (#186).
- Adres, telefoon en e-mail van leden en het tokenrecht `persoonsgegevens` zijn weg (#180).
- De lidpagina toont geen lijst "Aantal boten per bootsoort" meer (#179).
- Na een mislukte poging staat het wachtwoordblok op Uitnodiging en Profiel open (#188).

**Bijwerken vanaf 0.3.0** (zie `documentatie/beheer/bijwerken.md`). Maak eerst een back-up van de database.
- Migratie 0017 zet het logo in de database. Upload een bestaand logo één keer op Instellingen. De downgrade verwijdert een geüpload logo.
- Migratie 0018 verwijdert de contactgegevens van leden en het recht `persoonsgegevens`; een actief token met alleen dat recht wordt ingetrokken. De downgrade zet de gegevens niet terug.
- `docker-compose.yml` is gewijzigd (geen koppeling van `./huisstijl` meer, een router voor `/instellingen/logo`, variabelen voor e-boekhouden): haal hem opnieuw op bij de tag `v0.4.0`.
- Nieuw in `.env`, alleen bij `LEDENBRON=eboekhouden`: `EBOEKHOUDEN_USERNAME`, `EBOEKHOUDEN_CODE1`, `EBOEKHOUDEN_CODE2` en `BOOTAANTALLEN_SCHRIJVEN`. `LOGO_BESTAND` vervalt.

## 0.3.0 (2026-11-07)

Derde release van botenloodsbeheer: het nieuwe ontwerp in de Dajaks-huisstijl, nieuwe silhouetten in het rekoverzicht en de rekindeling en bezetting als CSV.

**Images** (linux/amd64), gescand met trivy vóór de push:
- `ghcr.io/reinoud/botenloods-app:0.3.0`
- `ghcr.io/reinoud/botenloods-integratie:0.3.0`

Ook beschikbaar onder de tags `0.3` en `latest`.

**Nieuw en gewijzigd**
- Dajaks-huisstijl (basis 0.3.0) met Rubik en PT Sans, alleen licht thema. De kleuren zijn niet meer instelbaar; naam en logo blijven dat wel (#150 deel 1).
- Kop en menu in drie groepen (Dagelijks, Registers, Beheer), rekoverzicht dat op een telefoon opzij schuift, plaatspagina in twee kolommen op een groot scherm, indeling met tabellen die op een telefoon kaarten worden (#150 deel 2, blok 1).
- Nieuwe silhouetten in het rekoverzicht: bezet gevuld, vrij alleen een omtrek, ook zonder kleur te onderscheiden (#155).
- Rekindeling als CSV: export, leeg sjabloon en import (#157).
- Bezetting als CSV: export, sjabloon en import met een koppelscherm dat koppelingen onthoudt (#158).
- Compose start niet meer als `docker/db-init.sh` ontbreekt (#156).

**Bijwerken vanaf 0.2.0** (zie `documentatie/beheer/bijwerken.md`). Maak eerst een back-up van de database.
- Migratie 0015 verwijdert de instelbare kleuren; de downgrade zet ze niet terug.
- Migratie 0016 voegt de tabellen voor de bezettingsimport toe; bestaande gegevens veranderen niet.
- `docker-compose.yml` is gewijzigd (lange syntaxis voor `docker/db-init.sh`): haal hem opnieuw op bij de tag `v0.3.0`.
- Geen nieuwe variabelen in `.env`.

## 0.2.0 (2026-11-06)

Tweede release van botenloodsbeheer: de indeling met rek, verdieping en vak, het rekoverzicht, het nieuwe kaartje en een reeks verbeteringen in beveiliging en beheer.

**Images** (linux/amd64), gescand met trivy vóór de push:
- `ghcr.io/reinoud/botenloods-app:0.2.0`
- `ghcr.io/reinoud/botenloods-integratie:0.2.0`

Ook beschikbaar onder de tags `0.2` en `latest`.

**Nieuw en gewijzigd**
- Indeling per rek met verdiepingen en vakken, met een bootsoort per verdieping (#80, #83, #94, #110).
- Rekoverzicht met een plaatje per plaats, bezet of vrij, per bootsoort (#87 en vervolg).
- Het kaartje toont de bootsoorten van de plaats, zonder omschrijving van het rek en zonder eigenaar (#143).
- Op de plaatspagina staan alleen boten die passen; een boot zonder plaats is toe te wijzen vanaf de bootpagina (#131, #132).
- Recente inlog voor blokkeren, deblokkeren en verwijderen van beheerders (#12); het recht `leden:importeren` alleen via de CLI (#55, #118).
- Load balancer vóór Traefik via het PROXY protocol (#54); gecodeerde tekens in het pad geweigerd (#127, #133).
- Basisimages op een digest, psycopg met libpq uit Debian (#25, #86, #124).

**Bijwerken vanaf 0.1.0** (zie `documentatie/beheer/bijwerken.md`). Maak eerst een back-up van de database.
- Migratie 0011 verwijdert alle bestaande rekken en plaatsen; boten blijven bestaan, zonder plaats. Bouw de indeling daarna opnieuw op.
- Migraties 0012 tot en met 0014 veranderen geen bestaande gegevens.
- `docker-compose.yml` is gewijzigd (postgres op een digest): haal hem opnieuw op bij de tag `v0.2.0`.
- Geen nieuwe variabelen in `.env`.

**Bekend:** zorg dat `docker/db-init.sh` als bestand op de host staat vóór de eerste start; ontbreekt het, dan maakt Docker er een map van en krijgen de databaserollen geen wachtwoord (#156, herstel in `documentatie/beheer/installatie.md`).

## 0.1.0 (2026-11-03)

Eerste release van botenloodsbeheer: slice 1 tot en met 11 en de restpunten van de securityronde.

**Images** (linux/amd64), gescand met trivy vóór de push:
- `ghcr.io/reinoud/botenloods-app:0.1.0`
- `ghcr.io/reinoud/botenloods-integratie:0.1.0`

Ook beschikbaar onder de tags `0.1` en `latest`. Zie `documentatie/beheer/voorbeelden.md` voor de installatie met deze images.

**Bekend:** psycopg-binary wordt na 2026-11-17 bijgewerkt (#63).
