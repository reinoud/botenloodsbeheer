# Terugblik aegis, review herstel slice 5

Datum: 2026-10-31. Taak: securityreview van het herstel van slice 5 (AEG-01, AEG-03, sleutel van de rate limit, logbesluit). Oordeel: akkoord.

## Wat ging goed

De draaiende nginx had dezelfde bestanden als de gestagede versie (met `cmp` gecontroleerd), dus de live proeven toetsen echt de diff. De positieve controle eerst (echt token vanaf `koppeling` geeft 200) maakte de 429 en 401 daarna betekenisvol.

## Wat kon beter

De opdracht vroeg om een geremde POST op `/uitnodiging/<code>` live na te spelen, en tegelijk om hooguit enkele verzoeken. De rem slaat pas aan na 21 POSTs. Die twee eisen botsen op de gedeelde nginx.

## Wat deed ik zelf goed

Ik heb de botsing opgelost met een losse nginx-container op de gestagede bestanden, met een eigen teller en een stub als upstream. Zo raakte de proef de teller van sentinel niet. Een mutant zonder `limit_req_log_level` liet in diezelfde container de code wel in de foutlog zien, dus de proef kan het lek echt zien.

## Wat heb ik onderweg verbeterd

Mijn eerste nep-proef las het token niet in (het script kwam via stdin binnen in plaats van het token). Ik zag dat aan 15 keer 401 zonder 429 en heb de proef opnieuw gedaan met het token via stdin.

## Wat kan structureel beter

Zet in de opdracht: "Een proef op een gedeelde rate limit doe je in een losse nginx-container op de gestagede bestanden (eigen teller, stub als upstream); de gedeelde nginx alleen voor proeven onder de grens."
