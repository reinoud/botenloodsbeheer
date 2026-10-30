# ADR-001 Inlogmethode voor beheerders

**Status:** Voorgesteld, besluit van de stakeholder nodig (architectuur §9, besluit 1)
**Datum:** 2026-10-30
**Stories:** BLB-022, BLB-023

## Context

Drie beheerders met gelijke rechten zien persoonsgegevens van 210 leden en beheren de loods. De intake vraagt een moderne en veilige inlogmethode. BLB-022 vraagt geen vast standaardwachtwoord bij een nieuwe installatie en een rem op herhaalde pogingen. BLB-023 vraagt dat een beheerder de toegang van een ander kan herstellen zonder dat iemand een wachtwoord ziet, en dat blokkeren een lopende sessie beëindigt.

Het grootste risico voor een kleine vereniging is een gestolen of hergebruikt wachtwoord en phishing. Een beheerder is een vrijwilliger, geen IT'er; een methode die veel uitleg of herstelwerk vraagt, wordt omzeild.

## Besluit

Beheerders loggen in met een passkey (WebAuthn), zonder wachtwoord. Een beheerder mag meerdere passkeys registreren, bijvoorbeeld op telefoon en laptop.

- **Account aanmaken:** een beheerder maakt een account aan; de applicatie toont een eenmalige uitnodigingslink, 24 uur geldig. De nieuwe beheerder opent de link en registreert een passkey. De database bewaart alleen de hash van de code in de link.
- **Eerste beheerder:** `flask beheerder uitnodigen <naam>` in de container geeft de eerste link. Zo bestaat er geen standaardwachtwoord.
- **Herstel:** wie geen werkende passkey meer heeft, krijgt van een andere beheerder een nieuwe uitnodigingslink. Zijn alle drie hun toegang kwijt, dan gebruikt iemand met servertoegang het CLI-commando. Herstel verwijdert de oude passkeys niet automatisch; de beheerder kan ze in zijn profiel intrekken.
- **Sessie:** na inloggen een ondertekende sessiecookie met beheerder-id en sessieversie (`Secure`, `HttpOnly`, `SameSite=Lax`), 12 uur geldig. Bij elk verzoek controleert de applicatie of het account actief is en de sessieversie klopt. Blokkeren hoogt de versie op en beëindigt zo elke sessie.
- **Rem op pogingen:** Nginx beperkt de inlog-endpoints per IP-adres. Met passkeys valt er niets te raden, dus een accountblokkade na mislukte pogingen is niet nodig.
- **Bibliotheek:** `webauthn` (py_webauthn) op de server, een klein eigen script met `navigator.credentials` in de browser. User verification is verplicht (pincode of biometrie op het toestel).

## Alternatieven

| Optie | Voordelen | Nadelen |
|-------|-----------|---------|
| Wachtwoord met TOTP | Bekend, werkt op elk toestel | Wachtwoord en TOTP-code zijn allebei te phishen; wachtwoordopslag, resetstroom en TOTP-geheimen beheren; meer code |
| Wachtwoord met passkey als tweede factor | Vertrouwd voor gebruikers | Alle nadelen van wachtwoordbeheer, terwijl de passkey alleen al sterker is |
| Passkey met wachtwoord als terugval | Werkt ook zonder passkey | De terugval is de zwakke plek; aanvallers kiezen die |
| Inloglink per e-mail | Geen wachtwoord | Vraagt een mailserver en maakt de mailbox de sleutel; phishing van de link mogelijk |
| Alleen passkeys (gekozen) | Phishingbestendig, niets te lekken, minste code, herstel via een andere beheerder past bij drie gelijke beheerders | Vraagt een toestel met passkey-ondersteuning; vaste domeinnaam met HTTPS nodig |

## Gevolgen

- Elke beheerder heeft een toestel met passkey-ondersteuning of een hardwaresleutel. Dit vraagt iets van de beheerders en is daarom een besluit van de stakeholder.
- Passkeys zijn gebonden aan de domeinnaam (`WEBAUTHN_RP_ID` in de omgeving). Verandert die, dan moeten alle beheerders opnieuw registreren. Zie architectuur §9, besluit 2.
- E2E-tests gebruiken de virtuele authenticator van Chromium; er komt geen inlogomweg.
- Aegis beoordeelt de inlogstroom en het herstel vóór de commit (overlay §4).
- Kiest de stakeholder voor wachtwoord met TOTP, dan vervalt de tabel `passkey` en komen een wachtwoordhash en een TOTP-geheim per beheerder erbij. De uitnodigingslink blijft de manier om een wachtwoord in te stellen. Het besluit raakt alleen slice 1 en is daarna moeilijk om te draaien zonder alle beheerders opnieuw te laten registreren.
