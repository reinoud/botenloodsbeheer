# Terugblik sentinel, review issue #24 (rijbeleid op taakrun)

**Datum:** 2026-11-05
**Taak:** review vóór de commit van migratie 0014, de test in `tests/unit/test_migratie_en_taken.py` en ADR-012 v1.7.0.

## Wat ging goed

De brief noemde het criterium letterlijk, de stand van de gedeelde database (al op 0014), wie de suite draait en de mutant van de regie. Daardoor kon ik direct de mutanten bouwen en hoefde ik niets na te vragen.

## Wat kon beter

De eerste mutant zonder beperkend beleid liet ook de downgrade ongemoeid. Die faalde daardoor op `DROP POLICY` in zes migratietests, wat de uitkomst vertroebelde. Een tweede, schone mutant (ook de `DROP POLICY` weg) faalde alleen op de assert van het criterium.

## Wat deed je zelf goed

Elke mutant draaide tegen de hele unitsuite, zodat voor vraag (b) zichtbaar werd welke bestaande test valt. Ik heb per mutant de falende regel genoemd en een databasefout apart gemeld van een assert met eigen melding.

## Wat heb je onderweg verbeterd

Na de vertroebelde eerste run heb ik mutant a2 toegevoegd. De controle op downgrade en upgrade toetst ook de inhoud van `pg_policies` en `relrowsecurity`, niet alleen de revisie.

## Wat kan structureel beter

Zet in de opdracht: "Een mutant die een object uit `upgrade()` weghaalt, haalt de bijbehorende regel uit `downgrade()` ook weg; anders faalt de mutant op de downgrade in plaats van op de assert van het criterium."
