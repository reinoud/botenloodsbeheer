"""Eerste import van een verse stack: de synthetische leden zonder opzegdatums (#220).
Sinds #203 slaat de import een nieuw lid met een opzegdatum over. Zonder deze stap heeft de seed
geen oud-leden. De tweede import, met de opzegdatums, volgt via de integratiecontainer of de API.
Omgeving: EERST_API (basis-URL van de API) en EERST_TOKEN (recht leden:importeren)."""

import json
import os
import urllib.request
from pathlib import Path

leden = json.loads(Path("/fixtures/leden.json").read_text(encoding="utf-8"))
verzoek = urllib.request.Request(
    f"{os.environ['EERST_API']}/leden", method="PUT",
    data=json.dumps({"leden": [{**lid, "opzegdatum": None} for lid in leden]}).encode(),
    headers={"Authorization": f"Bearer {os.environ['EERST_TOKEN']}",
             "Content-Type": "application/json"})
with urllib.request.urlopen(verzoek, timeout=60) as r:
    assert r.status == 200, r.status
    print(r.read().decode())
