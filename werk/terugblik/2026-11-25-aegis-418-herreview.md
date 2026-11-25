# Terugblik Aegis, herreview #418 deel 2 (vangnet)

Datum: 2026-11-25
Taak: security-herreview van de gestagede diff op `feature/418-vangnet`: herstel van AEG-01, de sectie Vangnet in `installatie.md` en de nieuwe `-p` in `tests/e2e/vangnet.sh`. Oordeel: akkoord.

## Wat ging goed

De opdracht noemde precies wat al akkoord was en wat nog getoetst moest worden. Daardoor bleef de review klein. De scratchmap van de eerste review stond er nog, met de opzet van de losse Traefik; die kon ik direct hergebruiken.

## Wat kon beter

Lokaal staat geen Python met pytest of PyYAML. De nieuwe unittest kon ik daarom niet zelf draaien zonder de stack `botenloods` te gebruiken, en die was bezet. Ik heb de regel met het oog vergeleken met die van `-web`.

## Wat deed je zelf goed

Ik heb de route geproefd in vijf toestanden (web aan of uit, `compose.api-extern.yml` aan of uit, api weg) met de echte Traefik-versie en het echte vangnet-image, ook met paden als `/API/`, `/%61pi/` en `//api/`. Het vangnet beantwoordt in geen enkele toestand een `/api/`-pad en geeft exact dezelfde dekking als `-web`. Containers en netwerk zijn opgeruimd.

## Wat heb je onderweg zelf verbeterd

Mijn eerste generator voor de Traefik-configuratie zette `\&\&` letterlijk in de regel. Ik zag dat in de uitvoer vóór het proeven en heb de generator herschreven, zodat de metingen op de juiste regels liepen.

## Wat kan structureel beter

Zet in de opdracht: "Noem hoe de reviewer een losse unittest draait zonder de gedeelde stack, of zeg dat de regie die test zelf draait."
