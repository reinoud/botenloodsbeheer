# Terugblik Bedrock, #206 Boot verplaatsen

Datum: 2026-11-13. Taak: bouw van #206 (ontwerp 5B) op `feature/206-boot-verplaatsen`, niet gecommit.

## Wat ging goed

- De opdracht verwees naar bestanden en commit (`6f4cabb`), dus het ontwerp was in één leesronde helder. De README bleek leidend voor klassen en teksten, de previews bevestigden de markup.
- De lijst van bestaande tests die breken (README, §"Breekt in het product") klopte: alleen `test_blok3b_detail.py` brak.
- De drie logweergaven die op een voorvoegsel filteren stonden snel in beeld door `grep` op `log.regels(`.

## Wat kon beter

- De opdracht noemde de previews onder `preview/`; ze staan onder `werk/product/dajaks/schermen/blok-5/preview/`. Eén `git ls-tree` loste dat op, maar het kostte een mislukte aanroep.
- `DRAAI_OVERRIDE` past de override niet toe op `web`: `draai.sh` maakt `web` niet opnieuw aan. De eerste twee E2E-mutanten slaagden daardoor onterecht. Ik ontdekte het pas door te controleren of de mutant in de container stond.
- Het script `schermafbeeldingen.py` verwacht dat de pagina na een stap op de plaats staat; mijn nieuwe stap liet hem op de boot staan en de run (ruim twee minuten) moest opnieuw.
- Een verwijdercommando voor één eigen, ongetrackt bestand werd door de omgeving geblokkeerd en kostte tien minuten wachttijd.

## Wat deed je zelf goed

- Het ontwerp liet een geval open: een boot van een oud-lid met een plaats. Ik heb het blok daar weggelaten en gemeld, in plaats van een misleidende zin "Er is geen vrije plaats" te tonen.
- De vergrendeling is op volgorde van id gezet, zodat twee verplaatsingen in tegengestelde richting elkaar niet laten vastlopen. De tweede racetest (oude plaats intussen vrijgegeven) dekt het herlezen na de vergrendeling.
- Elke test kreeg een mutant (15 in het domein en de web-laag, 3 op het sjabloon voor E2E) met de falende assert vooraf benoemd in de testcommentaren.

## Wat heb je onderweg verbeterd

- Mijn eerste versie van de wachtlijsttest bevatte een `hasattr`-omweg en een onduidelijke assert; vervangen door `erop_zetten` en een vergelijking van de tabelinhoud.
- Een testhulp telde dezelfde lidnummers dubbel (`lid()` zonder argument); `liggen()` neemt nu een lidnummer.
- De E2E-controle voor gh#50 stond eerst als assert in de test; omdat gh#50 nog speelt (zie opdrachtantwoord) is die assert eruit en staat er een commentaar met de verwijzing.

## Wat kan structureel beter, als regel voor de volgende opdracht

- Zet in de opdracht: "Paden in een bron buiten de repository noem je met het volledige pad op de genoemde commit, niet met een submap."
- Zet in de opdracht voor een E2E-mutant op een sjabloon: "Zet eerst `web` opnieuw aan met `-f compose.<mutant>.yml up -d --no-deps --force-recreate web` en controleer met `docker exec ... grep -c` dat de mutant draait; `DRAAI_OVERRIDE` doet dat niet." De overlayregel over `DRAAI_OVERRIDE` is hierop te verduidelijken.
- Zet in de opdracht voor een nieuwe schermafbeelding: "Het script moet na de nieuwe stap weer op de pagina staan waar de volgende stap begint."
- Zet in de opdracht: "Een equivalente mutant (zoals `rollback` na een weigering, dat in de unittest geen verschil geeft) mag het agent benoemen in plaats van te forceren."
