# Terugblik Bedrock, koppeling e-boekhouden (issue #178)

Datum: 2026-11-08. Taak: bron `eboekhouden` met zeep en terugschrijven van `def10`. Eerste ronde gestopt bij het stoppunt (bibliotheek kon geen relatie bijwerken); tweede ronde gebouwd na het besluit voor alleen zeep.

## Wat ging goed
De bibliotheek is vóór de bouw gelezen, zodat het ontbreken van een bijwerkaanroep vóór de eerste regel code bleek. De WSDL uit de opdracht bevatte alles voor het ontwerp: de typen, de volgorde van de velden voor de nagebootste server, en het http-adres.

## Wat kon beter
Ik begon de mutantrun terwijl ik nog aan bestanden werkte die de run zelf muteerde. Ik heb dat onderweg beperkt tot documentatie, maar een aparte werkkopie had dit voorkomen. Het eerste script gaf een lege uitkomst door `tail -1` op een lege regel; pas bij de tweede run viel dat op.

## Wat deed je zelf goed
- Bij het stoppunt stoppen, zonder een route via een privéattribuut te bouwen.
- Het adres vastzetten op https: de WSDL noemt http, en een lokale kopie had de inloggegevens onversleuteld verstuurd. Een test dekt het.
- zeep logt op DEBUG de inloggegevens in het verzoek; het logniveau staat daarom vast op WARNING, met een mutant die de test vangt.
- De nagebootste server beantwoordt de echte WSDL, zodat zeep het echte verzoek opbouwt en de test controleert wat er over de lijn gaat.

## Wat heb je onderweg zelf verbeterd
- Een foutsoort werd verkeerd ingedeeld (een 200 met onleesbaar antwoord gaf onbereikbaar); de tests lieten dat zien en de indeling is aangepast.
- De nep-API in de unitsuite viel om op `lichaam["leden"]` bij een ander pad; de dictionary rekende alle waarden uit. Aangepast naar een voorwaarde op het pad.
- Testmappen die de unitsuite leest (`.github`, `docker`, `pyproject.toml`, `uv.lock`) stonden niet in de container; een mutant liet dat zien en ze zijn gemount in `compose.dev.yml`.

## Wat kan structureel beter in de opdracht of de afspraken
- Zet in de opdracht: bij een besluit dat een bibliotheek kiest, controleert de regie vooraf in de broncode van de vastgepinde versie dat de benodigde aanroepen bestaan (lezen en schrijven), en noemt dat in de opdracht.
- Zet in de opdracht: bij een externe SOAP-dienst staat de WSDL vooraf in de scratchpad, en de opdracht noemt het adresschema (http of https) dat de dienst gebruikt.
- Zet in de opdracht: tests met een afhankelijkheid die niet in het testimage zit, krijgen vooraf een gekozen plek en een commando, en de brief noemt of de regie het via een extra compose-dienst mag draaien.
- Zet in de briefingchecklist: een mutantrun muteert bronbestanden; geen andere agent of de regie bewerkt die bestanden tijdens de run, en de run staat in een eigen werkkopie of worktree.
- Zet in de briefingchecklist: een nieuwe map of nieuw bestand dat een unittest leest, wordt in dezelfde ronde gemount in `compose.dev.yml`.
