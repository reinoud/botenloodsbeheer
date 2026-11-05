# Terugblik aegis, securityreview issue #54

**Datum:** 2026-11-05
**Taak:** securityreview van de gestagede diff op `fix/54-proxyprotocol` (PROXY protocol vóór Traefik) tegen issue #54 en ADR-013 v1.4.1.

## Wat ging goed

De brief noemde de routers naar `api`, de ADR-alinea, het besluit over `X-Forwarded-For` en het log van de bouwer. Het log dekte elk acceptatiecriterium met een herkomst per antwoord (Traefik of applicatie), zodat ik geen eigen Traefik hoefde te starten.

## Wat kon beter

De brief vroeg of een beheerder met de documentatie een onveilige opzet kan maken, maar noemde niet welke soorten load balancer (TCP-doorgifte, TLS-terminatie) binnen de scope vallen. Ik heb aangenomen dat beide kunnen.

## Wat deed ik zelf goed

Ik zag dat de proef "client als load balancer" al bewijst dat Traefik elke PROXY-kop van een vertrouwd adres gelooft, ook een kop die de client zelf meestuurt. Daarmee was de bevinding over een load balancer zonder `send-proxy` bevestigd zonder extra proef.

## Wat heb ik onderweg verbeterd

Ik had eerst een eigen proef met een TCP-relay gepland. Die bleek overbodig: voor Traefik is een relay zonder eigen kop niet te onderscheiden van de proefclient op het adres van de load balancer. Ik heb de proef geschrapt.

## Wat kan structureel beter

Zet in de opdracht: "Beschrijft de documentatie een vertrouwensinstelling (`trustedips`, een whitelist), noem dan in de brief welke voorwaarde aan de andere kant moet gelden (zoals: de load balancer stuurt op elke verbinding zelf een PROXY-kop) en laat de reviewer toetsen of de documentatie die voorwaarde noemt."
