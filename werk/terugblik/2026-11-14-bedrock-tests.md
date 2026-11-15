# Terugblik Bedrock bij de testissues #153, #149, #161 en #209

Datum: 2026-11-14. Taak: vier testissues in branch `fix/tests-153-149-161-209`.

## Wat ging goed

- De brief noemde per issue bestand, mutant en de regels uit de overlay. Daardoor was elk issue in één ronde af, behalve het weglezen van het lichaam bij #209.
- De mutanten van #149 en #209 draaien als bind mount over één bestand met een override. De werkmap bleef schoon.
- De mutant op de label `-25mb` valt met een duidelijke assert, ook als Traefik de kop doorlaat: een time-out wordt status `None` in de assert in plaats van een kale `TimeoutError`.

## Wat kon beter

- Ik wijzigde `tests/e2e/draai.sh` terwijl een run ervan bezig was. Bash leest een script tijdens het draaien, dus de run brak af met "onverwacht bestandseinde". Geen wijziging aan een script dat loopt.
- De eerste E2E-run faalde op een `web` met oude Python-code: het filter `lognamen` bestond voor de draaiende gunicorn nog niet (alleen sjablonen laden vanzelf). Ik heb `web` eenmaal herstart. De bouwer had dit in de brief moeten lezen, ook al stond de stack groen.
- Een override met alleen `DRAAI_OVERRIDE` plaatst een mutant niet: `draai.sh` maakt `web` niet opnieuw aan. Mijn eerste mutantrun voor #149 slaagde daardoor schijnbaar (de id-mutant leefde). Ik heb de mutant pas daarna gecontroleerd met `grep` in de container.
- `sed -i ''` werkt hier niet (GNU sed). Ik gebruikte daarna python3.

## Wat deed je zelf goed

- Na elke mutantrun controleerde ik in de container dat de mutant echt actief was (`grep -c` in `web`), en herstelde `web` daarna.
- Bij #149 draaien beide toestanden van de pagina (lijst of melding) door één assert met `or_`. Beide mutanten vallen op die assert, met de regel van de aanroep.
- Bij #209 staan de twee kanten van de buitengrens in één test, met de herkomst: 302 met `Location` en een melding in de sessie (applicatie), 413 zonder `Location` (Traefik).

## Wat heb je onderweg verbeterd

- De test van #161 laadt geen database meer; de scriptmap wordt rechtstreeks gelezen. De ongebruikte `nieuwe_database` in die test is weg; de import blijft voor andere tests.
- In de test van #153 staat een assert dat de ids uiteenlopen (`soort("Kajak") < soort("Canadese kano")`), zodat de test niet stil vervalt als de volgorde van de standaardsoorten verandert.

## Wat kan structureel beter in de opdracht

- Zet in de opdracht: "Wijzig `tests/e2e/draai.sh` niet terwijl een run ervan loopt; maak de wijziging vóór de eerste run."
- Zet in de opdracht: "Een mutant op de compose-labels of op een bestand in `web` vraagt `up -d --no-deps --force-recreate web` met dezelfde override, en daarna herstel; `DRAAI_OVERRIDE` alleen doet dat niet."
- Zet in de opdracht: "Start eerst `docker compose restart web` als de laatste wijziging in `app/*.py` van vóór de start van `web` ligt; gunicorn laadt alleen sjablonen opnieuw."
- Zet in de opdracht bij een mutant op weglezen van een lichaam: "Noem of de mutant stabiel valt; de RST-race van #91 is timingafhankelijk en niet te forceren met Content-Length alleen."
