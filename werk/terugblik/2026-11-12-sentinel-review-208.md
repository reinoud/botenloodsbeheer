# Terugblik Sentinel, review #208

Datum: 2026-11-12. Taak: review vóór de commit van `fix/208-blok-open` (blok Foto vervangen en Nieuwe boot open na een weigering).

## Wat ging goed

De brief noemde het ontwerp, de enige aanroeper van `foto_vervangen`, de verwachte falende asserts per mutant en het exacte draaicommando. Daardoor waren zes mutanten en twee testruns genoeg; elke mutant viel op de voorspelde regel.

## Wat kon beter

`ruff check` faalt in de testcontainer op de cache in `/app/.ruff_cache` (geen schrijfrecht). Met `--no-cache` werkt het. De standaardregels van ruff vangen lege regels tussen functies niet; die vond ik pas met `--preview --select E30`.

## Wat deed je zelf goed

Twee mutanten toegevoegd die de brief niet vroeg: "Kies een foto." als geslaagd behandelen, en `foto_vervangen` zonder `return True`. Beide vallen, dus ook de nieuwe terugkeerwaarde is gedekt. Ook nagekeken dat #207 gesloten is, zodat het blok Nieuwe boot niet meer verandert.

## Wat heb je onderweg verbeterd

De ruff-run opnieuw gedraaid met `--no-cache` in plaats van de fout als "geen lint" te laten staan.

## Wat kan structureel beter in de opdracht

Zet in de opdracht: draai ruff in de testcontainer met `ruff check --no-cache <paden>`; de cache in `/app` is niet beschrijfbaar.
