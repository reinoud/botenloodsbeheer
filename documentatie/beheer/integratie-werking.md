# Werking van de integratiecontainer

**Versie:** v1.0.0
**Datum:** 2026-11-08
**Bronnen:** ADR-004, ADR-012, ADR-013, issue #178

De integratiecontainer houdt de ledenlijst van de applicatie gelijk aan e-boekhouden en schrijft per lid terug hoeveel plaatsen dat lid in de loods heeft. Hij is de enige dienst die met e-boekhouden praat. De applicatie zelf kent e-boekhouden niet en bevat geen code ervoor.

## Samenwerking met Traefik en de API

De container staat op twee netwerken. Op `koppeling` ziet hij alleen Traefik, onder de naam `traefik`. Daarover gaan alle aanroepen naar de API, via het entrypoint `intern` op poort 8081. Traefik stuurt alleen `/api/v1/` vanaf het subnet `KOPPELNET` door naar de dienst `api`. De database en de dienst `api` zelf bereikt de container niet. Op `buiten` heeft hij verkeer naar e-boekhouden, en alleen daar.

Bij elke aanroep stuurt de container het robottoken mee uit `/run/secrets/api_token`. Hij leest dat bestand elke ronde opnieuw, dus een nieuw token vraagt geen herstart. Elke minuut vraagt hij of een beheerder een import heeft aangevraagd. Is dat zo, of is het tijdstip van de dagelijkse import gepasseerd, dan haalt hij de leden op uit e-boekhouden en stuurt hij ze in één keer naar de API. Gaat er iets mis bij e-boekhouden, dan meldt hij een van drie vaste redenen (onbereikbaar, onleesbaar of geweigerd) en geen tekst van e-boekhouden.

## Namen en nummers van leden

De container logt in bij e-boekhouden met de drie codes uit zijn omgeving en vraagt alle relaties op. Een relatie telt als lid als haar soort (veld `Def2`) begint met "actief" of "opgezegd", zoals `actief_gewoon`. Van elk lid geeft hij vier gegevens door: het lidnummer uit het veld `Code`, de naam uit het veld `Bedrijf`, de datum van lid worden uit `Def3` en de opzegdatum uit `Def7`. Adres, telefoon en e-mail neemt hij niet mee. De applicatie vult die velden dan leeg, ook bij een lid dat ze eerder had.

Datums moeten in e-boekhouden als JJJJ-MM-DD staan. Een record met een andere notatie telt in de API als ongeldig en wordt overgeslagen.

## Van bezetting naar vrij veld 10

De bezetting rekent de applicatie zelf uit. Per lid telt ze per bootsoort de boten met een toegewezen plaats; een boot op de wachtlijst en een clubboot tellen niet. Na elke geslaagde import vraagt de container deze aantallen op met `GET /bootaantallen`, maar alleen als `BOOTAANTALLEN_SCHRIJVEN` op `aan` staat. Standaard staat die schakelaar uit.

Per schrijfronde haalt de container de volledige records één keer vers op uit e-boekhouden, zet per lid in `Def10` de aantallen als tekst, bijvoorbeeld `{"Kajak": 1, "Canadese kano": 2, "Surfski": 0}`, en stuurt het record verder ongewijzigd terug met de aanroep UpdateRelatie. Is de tekst al gelijk aan wat er stond, dan schrijft hij niets. Een lidnummer dat e-boekhouden niet kent, slaat hij over. Na drie mislukte schrijfaanroepen achter elkaar stopt hij met schrijven. Een mislukte poging komt niet apart terug: de volgende poging is de volgende geslaagde import.

De container logt per ronde één regel met de aantallen geschreven, ongewijzigd, niet gevonden en fout, zonder gegevens van leden.

## Verbinding met e-boekhouden

De container gebruikt de bibliotheek zeep en een kopie van de WSDL van e-boekhouden in het image, dus hij heeft bij het starten geen verbinding nodig en schrijft niets naar schijf. De WSDL noemt een http-adres; de container gebruikt vast `https://soap.e-boekhouden.nl/soap.asmx`. Wijzigt e-boekhouden zijn interface, dan vervang je de kopie `integratie/koppeling/eboekhouden.wsdl` en bouw je het image opnieuw.
