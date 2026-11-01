# Terugblik Bedrock, boot wijzigen (issue #39)

Datum: 2026-11-01. Taak: `boot_wijzigen` met logactie `boot.gewijzigd`, web, tests en handleiding.

## Wat ging goed
- De opdracht noemde bronnen, volgorde van de vergrendeling en de gewenste tests precies. Ik hoefde niet te gokken.
- De bestaande `race`-helper en de meldingen in `toewijzing.py` waren direct bruikbaar.
- De docker-omgeving en de eigen stack voor schermafbeeldingen werkten in één keer.

## Wat kon beter
- Mijn eerste testopzet maakte een boot voor een oud-lid met `boot()`; die weigert oud-leden. Ik had eerst de bestaande toewijzingstest moeten lezen.
- De opdracht noemde niet dat een nieuwe E2E-test een eigen uitnodiging nodig heeft in `tests/e2e/draai.sh`. Dat zag ik pas bij het lezen van het script.

## Wat deed je zelf goed
- De meldingen voor "past niet bij de plaats" staan nu op één plek (`controleer_past` in `toewijzing.py`), gebruikt door `toewijzen` en `boot_wijzigen`.
- Twee racetests, elk met een eigen mutant die precies die test laat falen. Daarnaast drie grens- en oud-lidmutanten.

## Wat heb je onderweg verbeterd
- Eigenaar-keuze in het formulier toont een bestaand oud-lid als geselecteerde optie, zodat opslaan zonder wijziging van de eigenaar niet stil de eigenaar verandert.
- Ruff-meldingen in mijn eigen test opgelost; één bestaande melding buiten de diff gemeld.

## Wat kan structureel beter in de opdracht of de afspraken
- Zet in de opdracht: "Een nieuwe E2E-test die inlogt, krijgt een eigen soort in de lijst van `tests/e2e/draai.sh`."
- Zet in de opdracht: "Een domeinfunctie met een vaste vergrendelvolgorde die tegengesteld is aan een bestaande functie (hier boot-dan-plaats tegenover plaats-dan-boot in `toewijzen`): laat het agent het deadlockrisico melden en zeg of de regie daarvoor een issue aanmaakt."
- Zet in de opdracht: "Het script voor schermafbeeldingen maakt alle afbeeldingen opnieuw; zeg of onbedoeld gewijzigde afbeeldingen (leden, log) mogen blijven of teruggezet moeten worden."
