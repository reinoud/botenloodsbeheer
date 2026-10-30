# Terugblik forge: slice 1a (stack, inloggen en mutatielog)

Datum: 2026-10-30. Taak: GitHub-issue #1, slice 1a van botenloodsbeheer.

## Wat ging goed

De bronnen waren goed op elkaar afgestemd. ADR-001, ADR-006 en architectuur §4 en §6 gaven genoeg detail om zonder vragen te bouwen. Python 3.14 werkte met alle afhankelijkheden, dus terugvallen naar 3.13 was niet nodig. Beide suites slaagden bij de eerste volledige run: 42 unittests en 4 E2E-tests, zonder overgeslagen tests.

## Wat kon beter

Docker draaide niet bij de start en moest eerst worden opgestart. De E2E-tests kunnen de CLI niet zelf aanroepen vanuit het Playwright-image. Daarom maakt `tests/e2e/draai.sh` de uitnodigingen vooraf aan. De vierde E2E-test gebruikt de link uit de eerste test en hangt dus af van de volgorde. Het lockbestand had nieuwere versies dan ik kende (webauthn 3, SQLAlchemy 2.1). Ik heb de API eerst in de container nagekeken.

## Wat deed ik zelf goed

Ik heb de afscherming van het log in de database getest: de webrol krijgt "permission denied" op UPDATE en DELETE, de taakrol mag verwijderen. Een test met `alembic check` laat de suite falen als modellen en migratie uit elkaar lopen. Een test op downgrade en upgrade dekt de omkeerbaarheid. De eenmalige code van een uitnodiging staat niet in de toegangslog van Nginx.

## Wat heb ik onderweg verbeterd

Een uitnodiging werd eerst verbruikt vóór de controle van wachtwoord en code; ik heb de volgorde omgedraaid. Flask-WTF controleert onder HTTPS de Referer, dus `Referrer-Policy: no-referrer` had in productie elk formulier geweigerd; ik koos `same-origin`. Pagina's krijgen `Cache-Control: no-store`, omdat het TOTP-geheim bij het instellen op de pagina staat. De rate limit telt alleen POST-verzoeken, zodat het laden van pagina's geen pogingen opmaakt.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Controleer vóór de start of Docker draait en noem in de opdracht welke externe images (met versie) al lokaal staan."

Zet in de opdracht: "Bij een afwijking van een ADR die alleen namen of de plaats van een instelling raakt (zoals een omgevingsvariabele per dienst), mag het agent die doorvoeren en melden; foundation werkt de ADR daarna bij."
