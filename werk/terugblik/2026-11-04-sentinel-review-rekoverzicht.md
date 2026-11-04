# Terugblik sentinel, review Rekoverzicht (issue #87)

Datum: 2026-11-04. Taak: review van de gestagede diff voor issue #87, met mutanten en randgevallen.

## Wat ging goed

De brief noemde de leidende bronnen (definition of done en de reactie met besluiten), de stand van de suite en het pad naar `commando.txt`. Daardoor kon ik direct mutanten draaien zonder ze zelf te bouwen. Vijf van de acht mutanten draaiden binnen enkele minuten, elk met één vallende assert.

## Wat kon beter

Een losse test uit de scratchpad draaien kostte een extra ronde: `tests/` is read-only gemount en een bestand daarin mounten maakt een leeg bestand in de werkmap. Wat werkte: de scratchpad op `/app/scratch` mounten met `-e PYTHONPATH=/app` en `pytest -p tests.unit.conftest`.

## Wat deed ik zelf goed

Naast de mutanten van de bouwer heb ik de randgevallen zelf gerenderd (geen rekken, een rek zonder plaatsen, alleen een hogere verdieping) en de kopbalk van één schermafbeelding vergeleken met `HEAD`. Zo zag ik dat een verdieping zonder plaatsen uit het raster valt.

## Wat heb ik onderweg verbeterd

Ruff draaide eerst alleen op de standaardscope en meldde geen fouten. Door `docker/` apart te mounten zag ik zeven meldingen in `docker/maak_plaatjes.py` die de normale controle nooit ziet.

## Wat kan structureel beter

Zet in de opdracht: een nieuw Python-bestand buiten `app/` en `tests/` (zoals `docker/`) lint je met `-v $PWD/<map>:/app/<map>:ro` en `ruff check --no-cache <map>`, want de testcontainer mount die map niet.

Zet in de opdracht: een reviewer die een eigen test draait, mount de scratchpad op `/app/scratch` en draait `pytest -p tests.unit.conftest /app/scratch/<bestand>` met `-e PYTHONPATH=/app`, nooit een bestand onder `tests/`.
