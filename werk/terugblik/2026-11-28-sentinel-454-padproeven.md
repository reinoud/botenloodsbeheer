Datum: 2026-11-28. Taak: review vóór commit van issue #454, padproeven van ADR-013 als script (sentinel).

## Wat ging goed

- Eén run van `tests/proxy/padproeven.sh` op de gestagede stand: 134 geslaagd, 0 mislukt, exit 0, 337 s. Daarna geen containers of netwerken met `padtest`; de dev-stack draaide door met dezelfde uptime.
- De brief noemde de leidende bron (ADR-013) en de tweede bron (`werk/traefik-proeven.md`), dus de dekkingsvraag was per regel na te lopen.
- De mutant van de bouwer (`padproeven-mutant.sh`) stond met diff in de scratchpad; met één `diff` tegen de index was te zien dat alleen de verwachting veranderde.

## Wat kon beter

- De brief vroeg of het script faalt bij een proef zonder positieve controle vooraf, maar noemde niet dat `WACHT=1` die controle hoort te borgen. Dat het wachten in `pad()` ontbreekt, vond ik pas door `WACHT` in `klant.py` te zoeken.
- De bouwer en de regie telden de groene runs als bewijs voor de wachtlogica. Een run die toevallig snel genoeg is, bewijst niet dat er gewacht wordt.

## Wat deed je zelf goed

- De run direct in de achtergrond gestart en intussen statisch gereviewd, zodat de wachttijd niet verloren ging.
- Elke padparameter en elk gecodeerd pad uit `werk/traefik-proeven.md` (rijen 64 tot 70) naast de lus en de controles in het script gelegd. Zo kwam `/api/v1/%2Fik` als enige ontbrekende proef op websecure boven.
- Regellengtes met python3 op de index gemeten, gescheiden naar commentaar en code.

## Wat heb je onderweg zelf verbeterd

- Eerst wilde ik bij het einde van de run op een melding wachten. Ik ben overgestapt op een wachtlus op `exit=` in het uitvoerbestand, omdat een agent zonder die lus zijn beurt kan beëindigen voordat de melding komt.

## Wat kan structureel beter in de opdracht of de afspraken

- Zet in de opdracht: "Gebruikt een proefscript een omgevingsvariabele van `klant.py` (zoals `WACHT`), noem dan de functie die hem leest; de reviewer controleert dat elk subcommando die de variabele krijgt, hem ook leest."
