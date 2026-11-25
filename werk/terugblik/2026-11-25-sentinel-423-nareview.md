# Terugblik sentinel, nareview #423

Datum: 2026-11-25
Taak: nareview vóór commit van het herstel in de paragraaf Architectuur van `README.md` (zin over `api`, drie pijlen in het Mermaid-diagram) en van de verwijzing Beheer > Import/export in `documentatie/gebruikers/handleiding.md`.

## Wat ging goed

- De patch van de eerste review naast `git diff --cached README.md` leggen gaf in één diff precies de drie herstelde regels en de nieuwe zin. De rest van de diff hoefde ik niet opnieuw te lezen.
- Elke pijl liet zich tegen één label of regel leggen: `entrypoints=intern` en `ClientIP` van de router `api`, `API_URL=http://traefik:8081/api/v1` en `networks: [koppeling, buiten]` van `integratie`, `traefik.docker.network=..._voorkant` van `api`, en `entrypoints=websecure` in `compose.api-extern.yml`.
- De twee testbestanden slaagden: 7 geslaagd, 0 overgeslagen.

## Wat kon beter

- De Mermaid-syntax heb ik alleen statisch getoetst. Een renderer (`mmdc`) staat niet lokaal, en ophalen via `npx` vraagt een download met een headless browser. Voor één gestippelde pijl met een label tussen aanhalingstekens is dat te zwaar; de vorm `A -.->|"..."| B` is gedocumenteerde Mermaid-syntax.
- De opdracht noemde twee zinnen in de handleiding; het zijn er drie op `/import-export` plus de aanvraag van een import (regels 220, 226, 238 en 287). Dat is consistent, maar de telling in de opdracht klopte niet.

## Wat deed je zelf goed

- De menutekst Beheer > Import/export gecontroleerd in `app/web/templates/base.html` (regel 37) in plaats van de handleiding als bron te nemen.
- De woordtelling met een script gedaan, met en zonder de slotregel met de verwijzing naar `architectuur.md` (185 en 180), zodat de regie ziet welke telling ze bedoelde.

## Wat heb je onderweg zelf verbeterd

- Bij het nalopen van de pijlen viel op dat het label van de browser (`voorkant`) een netwerk noemt, terwijl het label van de client (`websecure`) een entrypoint noemt. Dat valt buiten de API en buiten het herstel, en de eerste reviewer keurde die regel goed. Ik meld het als advies en niet als afkeuring.

## Wat kan structureel beter in de opdracht of de afspraken

- Zet in de opdracht: "Geef bij een diagram aan of de pijllabels een netwerk of een entrypoint noemen, en houd dat gelijk voor alle pijlen naar Traefik."
- Zet in de opdracht: "Noem het aantal gewijzigde zinnen uit `git diff --cached -U0 <bestand>`, niet uit het hoofd."
