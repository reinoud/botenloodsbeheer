# Terugblik sentinel, review #156

Datum: 2026-11-07. Taak: gestagede diff van `fix/156-db-init` toetsen tegen issue #156 (koppeling `docker/db-init.sh` in de lange syntaxis, ophalen met `curl` in `voorbeelden.md`).

## Wat ging goed
- De brief noemde per punt wat te toetsen en wat de regie al had gedaan. Zo kon ik gericht een eigen proef doen zonder de unitsuite.
- Een eigen projectnaam (`s156rev`, `s156mut`, `s156curl`) en `INSTALLATIE=s156` in de proef-`.env` hielden de dev-stack buiten schot.

## Wat kon beter
- De brief vroeg naar de curl-commando's met HTTP 200, maar niet of het opgehaalde bestand ook werkt. Pas met het bestand zoals `curl` het neerzet (0644) kwam een verschil tussen Docker Desktop en Linux boven.

## Wat deed je zelf goed
- Naast de nieuwe syntaxis ook de oude als mutant gedraaid: die maakt de map `docker/db-init.sh`, de nieuwe niet. Zo toetst de proef echt het criterium.
- Na de start de rollen in `pg_authid` gecontroleerd in plaats van alleen `healthy`, want `db` werd ook healthy zonder rollen.

## Wat heb je onderweg verbeterd
- Na de stille fout op Docker Desktop de Linux-semantiek nagebootst (bestand 0644 in de containerlaag). Daar wordt het script gesourcet en krijgen de rollen een wachtwoord. Zo bleef de bevinding laag in plaats van een blokkade.

## Wat kan structureel beter
- Zet in de opdracht: "Toets een opgehaald of gekoppeld bestand ook met de rechten die de beschreven stap oplevert (zoals 0644 na `curl`), en controleer het resultaat in de database, niet alleen de status `healthy`."
