Datum: 2026-11-04. Taak: schermafbeeldingen slice 12 (issue #80) opnieuw maken met het testlogo.

## Wat ging goed
`compose.doc.yml` zette het testlogo goed; de kopbalk en de kaartjes tonen overal het testlogo. Zes volledige runs van het script, de laatste slaagde met 29 afbeeldingen.

## Wat kon beter
De oorzaak van de `FileNotFoundError` is niet bewezen. Drie runs faalden op een andere afbeelding (steeds na een paar geschreven bestanden), drie runs slaagden. De map bestond op de host en in een losse container met dezelfde mount schreven 60 bestanden zonder fout. Een dubbele sentinelcontainer (alpine) die ik zelf startte, kon ik niet als oorzaak aanwijzen: runs zonder die container slaagden ook. Meest waarschijnlijk een tijdelijke storing van de bind mount (Docker Desktop) of gelijktijdige gitacties van andere agents in dezelfde map. Ik heb het script niet aangepast.

## Wat deed je zelf goed
Alleen de fout reproduceren en uitsluiten wat het niet was, in plaats van het script op een vermoeden om te bouwen. Tijdelijke proefbestanden alleen via Python verwijderd en mijn eigen container op id gestopt.

## Wat heb je onderweg zelf verbeterd
Een `timeout` rond `docker run` stopt alleen de CLI, niet de container: die bleef doorlopen en schreef in de map. Daarna op id gestopt. `git status` toont `boot.png` niet meer: na opnieuw maken is die identiek aan HEAD.

## Wat kan structureel beter
Zet in de opdracht: "Werk niet tegelijk met andere agents in `documentatie/gebruikers/afbeeldingen/` en laat tijdens de run geen git-checkout of stash in die repository lopen." En: "Bij een FileNotFoundError op de mount: draai het script opnieuw; meld pas een oorzaak als die bewezen is." Overweeg een `--retry` of `docker cp` uit de e2e-container als de storing terugkomt.
