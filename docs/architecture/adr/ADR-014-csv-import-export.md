# ADR-014 CSV-import en -export van rekindeling en bezetting

**Status:** Voorgesteld
**Datum:** 2026-11-06
**Versie:** v0.2.1
**Stories:** issue #157 (rekindeling), issue #158 (bezetting)

## Context

Beheerders willen indeling en bezetting via CSV overzetten en bewaren (besluiten stakeholder 2026-11-06). De bezetting bevat namen en lidnummers: externe invoer met persoonsgegevens (overlay §8). Overlay §6 legt imports en exports bij de integratiecontainer (ADR-012). Dat kader gaat over koppelingen met andere systemen. Een bestand dat een ingelogde beheerder uploadt of downloadt, hoort bij `web`, net als de Excel-export (open vraag 5).

## Besluit

### 1. Bestandsformaat

Het voorstel uit de issues blijft.

| Bestand | Kopregel |
|---------|----------|
| Rekindeling | `rek;omschrijving;verdieping;vak;bootsoorten;clubplaats`, één regel per plaats; `bootsoorten` gescheiden door `/` (leeg is geen bootsoort, alleen bij een nieuwe plaats of een plaats die al geen bootsoort heeft, zoals op het scherm), `clubplaats` is `ja` of `nee` |
| Bezetting | `plaats;boot;bootsoort;eigenaar;lidnummer`, één regel per bezette plaats; `lidnummer` optioneel; een clubboot heeft beide leeg |

| Onderwerp | Regel |
|-----------|-------|
| Scheidingsteken | Puntkomma; een kopregel zonder puntkomma geeft "verkeerd scheidingsteken" |
| Codering | Export UTF-8 met BOM. Import leest UTF-8 met of zonder BOM, anders "sla op als CSV UTF-8". Geen gok naar Windows-1252 |
| Commentaar | Een regel waarvan de eerste cel na inlezen met `#` begint; dat werkt ook als Excel de cel tussen aanhalingstekens zet. De lege export heeft uitleg, toegestane bootsoorten, een voorbeeldregel als commentaar en de kopregel |
| Kolommen | Precies die van de kopregel, volgorde vrij |
| Grenzen | Hooguit 256 kB (de route leest niet verder) en 2000 regels. Alleen `.csv`, gecontroleerd op inhoud. Veldlengtes als in het model. Een stuurteken of regeleinde in een veld is een fout; naam, omschrijving en bootsoort weigeren stuurtekens ook op het scherm, zodat een rondgang altijd slaagt |
| Formules | Een exportcel die begint met `=`, `+`, `-`, `@`, tab of CR krijgt een `'` ervoor; de import haalt precies die `'` weg, zodat een rondgang niets verandert |

Omdat `/` de bootsoorten scheidt, weigert `_soortnaam` voortaan een `/`; een bestaande soort met `/` moet eerst hernoemd worden voor de export. Een reknaam die met `#` begint, is commentaar en dus een fout.

### 2. Rekindeling (#157)

**Alles of niets.** De import valideert het hele bestand en verzamelt per regel de reden van elke fout, in twee rondes: eerst de opbouw van elke regel, daarna de controles die de database vragen (bootsoort, gat, bezette plaats), hooguit 50 meldingen. Bij één fout verandert er niets en toont het scherm de lijst. Anders volgt alles in één transactie met één commit. Een lege export verandert niets.

**Herkennen.** Een rek aan zijn naam zonder verschil in hoofdletters (ADR-003), een plaats aan rek, verdieping en vak. Een andere naam is een nieuw rek; hernoemen kan alleen in het scherm. De omschrijving is binnen één rek gelijk. Plaatsen buiten het bestand blijven (besluit stakeholder).

**Hergebruik.** `rek_aanmaken`, `rek_wijzigen` en `plaats_wijzigen` krijgen een kern zonder commit en rollback; de publieke functies roepen die aan en houden hun gedrag. De import gebruikt de kernen, `_plaatsen_erbij`, `_naam`, `_omschrijving`, `_vakken` (geen gat na samenvoegen van bestaande en nieuwe vakken) en de controles uit `plaats_wijzigen` (een bezette plaats blijft geschikt voor haar boot en houdt haar clubplaats), die naar één gedeelde functie gaan.

**Vergrendelen en loggen.** Eerst de bestaande rekken (`FOR UPDATE`, oplopend op id), dan hun plaatsen, dan bootsoorten met `KEY SHARE`, zoals `indeling_instellen`. De bestaande logregels blijven, plus `indeling.geimporteerd` met alleen aantallen in het technische log.

### 3. Bezetting (#158)

**Lopende import.** Na de upload staat de import in tabel `bezettingsimport`, niet in de cookie: ingelezen regels en keuzes als JSON, niet het ruwe bestand. Hooguit één voor de hele installatie (stakeholder 2026-11-06, open vraag 3): elke beheerder ziet de lopende import en kan koppelen, bevestigen of annuleren, dus de routes dragen geen id. De tabel bewaart wie uploadde (`beheerder_id`) en toont dat in het overzicht. Een nieuwe upload terwijl er een loopt, wordt geweigerd met een melding dat eerst de lopende import bevestigd of geannuleerd moet worden. Bevestigen vergrendelt de rij, zodat twee beheerders niet tegelijk bevestigen. Verlooptijd 2 uur. `web` verwijdert verlopen rijen bij elke upload en elk koppelscherm, de dagelijkse opschoning (ADR-006) ook.

**Koppelen.** Volgorde: lidnummer, onthouden koppeling, exacte naam (zonder spaties aan begin en eind). Eigenaar en lidnummer leeg is een clubboot. Zonder precies één treffer komt de regel in het koppelscherm: lid (uit `leden.actieve_leden()`), clubboot of overslaan.

**Onthouden.** Tabel `naamkoppeling`: `naam` (uniek), `lid_id` (FK, `ON DELETE CASCADE`) of `clubboot`, `gebruikt_op`; een check eist precies één van beide. Overslaan wordt niet onthouden. De opschoning verwijdert koppelingen die 5 jaar niet zijn gebruikt (open vraag 4). Beheerders zien de lijst en verwijderen per koppeling.

**Boot herkennen.** Zelfde naam zonder verschil in hoofdletters en zelfde eigenaar. Geen treffer is een nieuwe boot, meer dan één een fout. Een afwijkende bootsoort is een fout; de import wijzigt geen boot.

**Overzicht vóór bevestigen.** Elke regel krijgt één uitkomst:

| Uitkomst | Betekenis |
|----------|-----------|
| ongewijzigd | Boot ligt al hier |
| toewijzen | Plaats is vrij |
| overschrijven | Huidige boot gaat van de plaats en blijft bestaan (besluit 2) |
| verplaatsen | Boot ligt elders en komt hierheen (open vraag 2) |
| nieuwe boot | Aanmaken en toewijzen (besluit 1) |
| overgeslagen | Keuze van de beheerder |
| te koppelen | Nog geen lid gekozen |
| fout | Onbekende plaats of bootsoort, melding van `controleer_past`, oud-lid, plaats of boot dubbel in het bestand, boot niet eenduidig |

Bevestigen kan pas zonder `te koppelen` en `fout`; zo'n regel slaat de beheerder over.

**Bevestigen, alles of niets.** Eén transactie:

1. Nieuwe boten aanmaken (kern van `boot_aanmaken`).
2. Vergrendelen zoals `toewijzen`: alle betrokken boten (uit het bestand en huidige bewoners) oplopend op id, daarna alle betrokken plaatsen (doel en herkomst) oplopend op id. Zo lopen twee imports niet op elkaar vast.
3. Elke regel opnieuw controleren.
4. Alle vrijgaven (kern van `vrijgeven`), daarna alle toewijzingen (kern van `toewijzen`, met `wachtlijst.na_toewijzen`).
5. Koppelingen onthouden, lopende import verwijderen, logregel, commit.

Faalt een controle, dan volgt een rollback en een nieuw overzicht.

**Oud-lid.** Ligt de boot van een oud-lid al op de plaats, dan is de regel `ongewijzigd`. Een nieuwe toewijzing of boot voor een oud-lid is een fout, zoals in `toewijzen` (open vraag 1).

**Loggen.** De bootmutaties krijgen de bestaande regels van de hergebruikte kernen. Het technische log krijgt `bezetting.geimporteerd` met alleen aantallen en `naamkoppeling.verwijderd` met `lid:<id>` of `clubboot`. Geen naam of veld uit het bestand komt in het technische log of in stdout, hooguit regelnummer en foutcode. Beide acties komen in `TECHNISCH`.

### 4. Rechten en migratie

Migratie `0016` (na `0015` van de open branch; anders volgt het nummer de head) maakt beide tabellen.

| Rol | `bezettingsimport` en `naamkoppeling` |
|-----|---------------------------------------|
| `botenloods_web` | SELECT, INSERT, UPDATE, DELETE, gebruik van de reeks |
| `botenloods_taken` | SELECT, DELETE |
| `botenloods_api` | geen |

`web` krijgt geen extra recht op `lid`: de import leest leden en wijzigt ze niet. De downgrade verwijdert beide tabellen met hun rechten. De migratietest doet upgrade, downgrade, upgrade. Een test bewijst dat de cascade werkt als de opschoning als `botenloods_taken` een lid verwijdert (zekerheid: Probable).

### 5. Webroutes

| Route | Methode | Doel | Vereist |
|-------|---------|------|---------|
| `/rekindeling.csv` | GET | Export, `?leeg=1` voor het sjabloon | inlog |
| `/rekindeling/import` | POST | Upload en uitvoeren | recente inlog |
| `/bezetting.csv` | GET | Export, `?leeg=1` voor het sjabloon | inlog |
| `/bezetting/import` | POST | Upload | recente inlog |
| `/bezetting/import` | GET | Koppelscherm en overzicht | inlog |
| `/bezetting/import/koppelen` | POST | Keuzes opslaan | inlog |
| `/bezetting/import/bevestigen` | POST | Uitvoeren | recente inlog |
| `/bezetting/import/annuleren` | POST | Lopende import weg | inlog |
| `/bezetting/koppelingen` | GET | Onthouden koppelingen | inlog |
| `/bezetting/koppelingen/<id>/verwijderen` | POST | Koppeling weg | inlog |

Elke POST heeft CSRF (ADR-011). Na opnieuw inloggen blijft de lopende import staan. Knoppen op `/indeling`; schermen volgens het Dajaks-ontwerp (#150) en de afwerklijst van overlay §4.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Lopende import in de sessiecookie | Persoonsgegevens in de browser, weg na opnieuw inloggen |
| Bezetting per regel uitvoeren | Een half verwerkt bestand is lastig te herstellen; per regel kiest de beheerder al in het koppelscherm |
| Import via integratiecontainer en API | De API zou schrijvende routes voor boten en plaatsen krijgen |

## Gevolgen

- De opschoning verwijdert ook verlopen imports en ongebruikte koppelingen en telt die in `taakrun`.
- Regressie: toewijzen, vrijgeven, wachtlijst, rekoverzicht, kaartjes, Excel-export, openbare pagina.

## Open vragen voor de stakeholder

De standaard geldt tot een besluit.

| # | Vraag | Blokkerend | Standaard |
|---|-------|------------|-----------|
| 1 | Mag een oud-lid via de import een plaats of nieuwe boot krijgen? | Besloten | Nee, zoals `toewijzen` (stakeholder 2026-11-06) |
| 2 | Boot uit het bestand die elders ligt: verplaatsen of fout? | Besloten | Verplaatsen, zichtbaar in het overzicht (stakeholder 2026-11-06) |
| 3 | Ziet elke beheerder een lopende import, of alleen de uploader? | Besloten | Elke beheerder; één lopende import voor de installatie (stakeholder 2026-11-06) |
| 4 | Bewaartermijn van onthouden koppelingen | Besloten | Weg met het lid, en 5 jaar na laatste gebruik (stakeholder 2026-11-06) |
| 5 | Betreft "imports en exports in de integratiecontainer" alleen koppelingen met andere systemen? | Besloten | Ja (regie 2026-11-06, volgt de standaard); overlay §6 verduidelijkt |

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v0.2.1 | 2026-11-06 | Fouten in twee rondes; lege cel `bootsoorten`; stuurtekens ook op het scherm geweigerd | Bouw en review #157 |
| v0.2.0 | 2026-11-06 | Open vragen besloten; één lopende bezettingsimport voor de installatie, zichtbaar voor elke beheerder | Besluiten stakeholder |
| v0.1.0 | 2026-11-06 | Eerste versie | Issues #157 en #158 |
