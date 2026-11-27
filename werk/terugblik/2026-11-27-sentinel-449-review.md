# Terugblik sentinel, review #449 (TZ in de e2e-container)

**Datum:** 2026-11-27
**Taak:** review vóór commit van `compose.dev.yml` en `docs/PROJECT-OVERLAY.md` voor #449. Oordeel: akkoord.

## Wat ging goed
De opdracht noemde de vier testbestanden, de uitvoer van de E2E-run en welke controle in de container mocht. Daardoor hoefde ik niets opnieuw te draaien en kon ik me op de compose-samenvoeging richten.

## Wat kon beter
Criterium 2 vraagt om een nagespeelde klok. De regie toetste de tijdzone met een vast tijdstip, niet met een stilgezette klok van app en test samen. Dat is redelijk, maar de reden staat nog nergens: die hoort bij het sluiten in het issue.

## Wat deed ik zelf goed
Ik toetste de grens aan beide kanten (23:59:59 en 00:00:01 CET) in de e2e-container. Met `docker compose config` met de release-override erbij zag ik dat de e2e-dienst `TZ` erft, en dat app en test dezelfde uitdrukking `${TZ:-Europe/Amsterdam}` gebruiken.

## Wat heb ik onderweg verbeterd
Ik zocht in de overlay naar de oude termen (23:00, middernacht). De oude regel is volledig vervangen.

## Wat kan structureel beter in de opdracht
Zet in de opdracht: "Kan een acceptatiecriterium niet letterlijk worden nagespeeld, noem dan in de opdracht de reden die de regie bij het sluiten in het issue zet, zodat de reviewer die kan toetsen."
