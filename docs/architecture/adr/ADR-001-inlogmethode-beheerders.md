# ADR-001 Inlogmethode voor beheerders

**Status:** Aanvaard, 2026-10-30 (besluit van de stakeholder; architectuur §9, besluit 1)
**Datum:** 2026-10-30
**Stories:** BLB-022, BLB-023

## Context

Drie beheerders met gelijke rechten zien persoonsgegevens van 210 leden en beheren de loods. BLB-022 vraagt geen vast standaardwachtwoord bij een nieuwe installatie en een rem op herhaalde pogingen. BLB-023 vraagt dat een beheerder de toegang van een ander kan herstellen zonder dat iemand een wachtwoord ziet, en dat blokkeren een lopende sessie beëindigt.

Foundation raadde alleen passkeys aan. De stakeholder besloot op 2026-10-30 dat een beheerder inlogt met een passkey of met een wachtwoord plus TOTP, en dat beide beschikbaar zijn. Een beheerder is een vrijwilliger, geen IT'er; de oplossing blijft daarom klein, zonder extra methodes.

## Besluit

**Keuze.** Bij de uitnodiging kiest de nieuwe beheerder: een passkey, een wachtwoord met TOTP, of beide. In het profiel voegt hij later een methode toe of trekt er een in. Elke beheerder houdt minstens één volledig ingestelde methode. Een wachtwoord zonder TOTP bestaat niet. Het inlogscherm toont beide mogelijkheden. Een passkey (WebAuthn, user verification verplicht) is één stap. Het wachtwoord vraagt daarna de TOTP-code.

**Uitnodigingslink.** Een beheerder maakt een account aan en de applicatie toont één link: 32 willekeurige bytes, 24 uur geldig, één keer te gebruiken. De database bewaart alleen de hash. De eerste beheerder komt uit `flask beheerder uitnodigen <naam>`; er is geen standaardwachtwoord.

**Wachtwoord.** Opslag als argon2id (`argon2-cffi`, standaardparameters, automatisch herhasht bij te zwakke parameters). Lengte 12 tot 128 tekens, geen samenstellingsregels, niet gelijk aan gebruikersnaam of naam. Een fout geeft altijd dezelfde melding; ook bij een onbekende gebruikersnaam rekent de applicatie een hash door, zodat de duur niets verraadt.

**TOTP.** RFC 6238 (`pyotp`), zes cijfers, 30 seconden, een stap marge. Het geheim staat versleuteld in de database (Fernet, sleutel `TOTP_SLEUTEL` uit de omgeving, ADR-009). De beheerder scant een QR-code (segno) en activeert pas na één juiste code. De applicatie bewaart de laatst gebruikte tijdstap en weigert die tweede keer. Er komen geen herstelcodes; herstel loopt via een andere beheerder.

**Brute force.** Nginx beperkt de inlog-endpoints per IP-adres. Daarnaast telt de applicatie per account opeenvolgende mislukte wachtwoord- en TOTP-pogingen. Na vijf weigert ze 15 minuten elke wachtwoordinlog voor dat account. Passkeyinlog blijft werken, dus de teller kan een beheerder met passkey niet buitensluiten.

**Herstel.** Een andere beheerder kan voor een collega een herstellink maken. Dat trekt direct alle passkeys, het wachtwoord, het TOTP-geheim en alle sessies van de collega in. De collega stelt via de link opnieuw een methode in. De helper ziet nooit een wachtwoord of geheim en kan zijn eigen account niet zo herstellen. Elk herstel krijgt een logregel. Zijn alle drie hun toegang kwijt, dan gebruikt iemand met servertoegang het CLI-commando.

**Sessie.** Ondertekende cookie met beheerder-id en sessieversie (`Secure`, `HttpOnly`, `SameSite=Lax`), 12 uur geldig. Elk verzoek controleert of het account actief is en de versie klopt. Blokkeren en herstel hogen de versie op.

## Alternatieven

| Optie | Reden |
|-------|-------|
| Alleen passkeys (eerste aanbeveling) | Door de stakeholder verlaten: niet elke beheerder wil of kan een passkey gebruiken |
| Herstelcodes of e-mailreset | Extra opslag, mailserver en aanvalsvlak; een andere beheerder lost het al op |
| Wachtwoord zonder TOTP | Te zwak voor persoonsgegevens |
| SMS of push als tweede factor | Externe dienst en kosten per installatie |

## Gevolgen

- Restrisico: wachtwoord met TOTP is te phishen, een passkey niet. De stakeholder accepteerde dit. Beheerders met een geschikt toestel krijgen het advies de passkey te kiezen; afdwingen doet de applicatie niet.
- Passkeys hangen aan de domeinnaam (`WEBAUTHN_RP_ID`). Besloten: elke installatie heeft een vaste domeinnaam met HTTPS (architectuur §9, besluit 2). Wijzigt die, dan registreren alle passkeygebruikers opnieuw.
- Tabel `beheerder` krijgt wachtwoordhash, versleuteld TOTP-geheim, laatste tijdstap, teller en blokkeertijd (architectuur §4).
- E2E-tests gebruiken de virtuele authenticator van Chromium en `pyotp` met een testgeheim; er komt geen inlogomweg.
- Aegis beoordeelt inlog, TOTP, brute-forceregels en herstel vóór de commit (overlay §4).
