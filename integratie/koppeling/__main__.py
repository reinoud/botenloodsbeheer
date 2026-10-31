"""python -m koppeling: de lus van de integratiecontainer (ADR-012)."""

import logging
import os
import signal
import sys
import time

from koppeling import Koppeling, instellingen, log

RONDE = 60  # seconden; ook de wachttijd zonder token

logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format="%(asctime)s %(levelname)s %(message)s")
# Als PID 1 negeert Python SIGTERM zonder eigen handler; zo stopt de container meteen.
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

try:
    cfg = instellingen(os.environ)
except ValueError as fout:
    sys.exit(f"Instelling ongeldig: {fout}")
if cfg["bron"] is None:
    log.warning("Geen ledenbron ingesteld (LEDENBRON is leeg); de container roept de API niet "
                "aan.")
    while True:
        time.sleep(3600)

log.info("Integratiecontainer gestart; API %s.", cfg["api_url"])
koppeling = Koppeling(cfg)
while True:
    koppeling.ronde()
    time.sleep(RONDE)
