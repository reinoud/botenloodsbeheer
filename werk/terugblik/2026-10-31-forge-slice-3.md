# Terugblik forge, slice 3

**Datum:** 2026-10-31 (begonnen 2026-10-30, onderbroken door de regie)
**Taak:** slice 3 bouwen (issue #13): BLB-015, 016, 017, 018, 019 en 027, met BLB-011 criterium 2 en BLB-003 criterium 1 uit slice 2.

## Wat ging goed

De bestaande opbouw droeg het werk. Domeinfuncties, `uitvoeren`, `recent_ingelogd`, de logmacro en de kaartweergave van tabellen op een telefoon waren er al. De indeling op het scherm (BLB-016) was een uitbreiding van de bestaande tabel, zonder nieuw scherm. Geen migratie nodig: de webrol had al alle rechten op `instelling` en `afbeelding`. Na de onderbreking klopte de werkmap precies met wat ik had achtergelaten.

## Wat kon beter

Twee keer liep ik vast op dezelfde valkuil: `from app.web import instellingen` gaf de domeinmodule terug die al onder die naam in `app.web` stond, en daarna gebeurde hetzelfde met de functie `huisstijl`. De route bestond dan niet, zonder foutmelding. Ook liet de eerste E2E-run met een fout de huisstijl van de dev-stack op geel staan; ik heb die met de hand teruggezet. De eerste racetest overleefde beide mutanten: `INSERT ... ON CONFLICT DO NOTHING` wacht zelf al op een vergrendelde rij, en een niet vastgehouden object valt uit de identity map.

## Wat deed ik zelf goed

Elke racetest heb ik met een mutant gecontroleerd in plaats van op het groene resultaat te vertrouwen. Daardoor zag ik dat de eerste versie niets bewees. Bij de Excel-export heb ik formule-injectie via een naam uit de ledenbron afgevangen en getest; dat stond niet in de story. De afwijking van ADR-002 (stylesheet in plaats van nonce) heb ik gekozen omdat de CSP van Nginx dan ongewijzigd blijft, en gemeld.

## Wat heb ik onderweg verbeterd

De racetest houdt nu de rij en het oude logo vast in de sessie, zoals een pagina dat doet; zonder `populate_existing` faalt hij dan. De melding voor recente inlog is algemeen gemaakt ("om dit te wijzigen"), omdat ze nu ook voor instellingen geldt. De seed logt de naam met dezelfde verwijzing (`instelling:huisstijl`) als het instellingenscherm. Het logo met CMYK wordt nu omgezet in plaats van geweigerd.

## Wat kan structureel beter in de opdracht of de afspraken

- Zet in de opdracht: "Een E2E-test die gedeelde instellingen wijzigt, zet ze ook terug als hij faalt (try/finally), of krijgt een eigen installatie."
- Zet in de opdracht: "Geef een nieuwe webmodule geen naam die al bestaat in `app.web` (zoals een domeinmodule of functie); controleer na het toevoegen dat de route bestaat met `flask routes` of een unittest."
- Zet in de opdracht: "Een racetest moet falen met een mutant zonder de vergrendeling; overleeft de mutant, meld dan waarom de vergrendeling toch nodig is."

## Correctie door de regie (2026-10-31)

De racetest op het vervangen van het logo faalt wel zonder `FOR UPDATE`: sentinel zag de mutant 3 van 3 keer falen. De volledige unitsuite gaf bij oplevering 215 geslaagd en 1 error (open verbinding uit `migrations/env.py`); de regie herstelde dat met `NullPool`.
