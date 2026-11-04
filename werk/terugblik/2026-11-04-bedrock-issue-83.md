# Terugblik Bedrock, issue #83 (bootsoort per verdieping, plaats verwijderen vervalt)

Datum: 2026-11-04. Taak: bouw van issue #83 volgens ADR-003 v2.2.0.

## Wat ging goed
- De ADR was concreet genoeg om zonder ontwerpvragen te bouwen: tabel, rechten, migratie en gedrag stonden erin.
- De zes mutanten (geen soort bij aanmaken, geen soort bij instellen, geen rij, geen controle op bestaande soort, geen filter op verdiepingen zonder vak, clubplaats aan) werden alle gevangen.

## Wat kon beter
- `uitvoeren()` in `app/web/__init__.py` plakt de actor achteraan de positionele argumenten. Mijn eerste opzet gaf `rek_aanmaken` een keyword-argument en brak daarop; dat had ik vooraf in de helper kunnen lezen.
- De opdracht noemde niet dat `rek_aanmaken` ook door `app/seed.py` en `tests/unit/hulp.py` wordt aangeroepen. Ik heb de signatuur daarom compatibel gehouden (nieuw argument achteraan, met standaardwaarde).

## Wat deed je zelf goed
- Het slot op de bootsoort (`FOR KEY SHARE`) staat ook in `indeling_instellen`, niet alleen in `rek_aanmaken`; anders kan `bootsoort_verwijderen` tussen lezen en schrijven een FK-fout geven.
- Logvelden `bootsoorten` komen alleen in het logregel als er een keuze is, zodat bestaande logtests en logregels gelijk blijven.

## Wat heb je onderweg verbeterd
- Een test die door een kleine opzet rommelig werd (`if False else None`) heb ik gesplitst in twee heldere tests.
- `TABELLEN` in `tests/unit/conftest.py` bevat nu `verdieping_bootsoort`, zodat de tabel na elke test leeg is.

## Wat kan structureel beter
- Zet in de opdracht: "Een nieuwe parameter van een domeinfunctie die via `uitvoeren()` wordt aangeroepen, gaat als keyword via `functools.partial`, want `uitvoeren` voegt de actor als laatste positionele argument toe."
- Zet in de opdracht: "Noem bij elke wijziging van een domeinfunctiesignatuur alle aanroepers (web, seed, testhulp)."
