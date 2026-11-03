"""Toegangslog van Gunicorn in het formaat zonder_code (ADR-013, #5, #14).

Eén regel per verzoek: adres, tijd, methode, pad, status en bytes. Het pad staat er zonder
querystring (geen zoektermen) en de code van een uitnodiging is gemaskeerd. Een pad met
procentcodering staat er tot het eerste %, zodat ook /%2Fuitnodiging/<code> geen code toont (#72). De healthcheck van
Docker zelf (zonder proxy) komt er niet in. Het adres is dat van ProxyFix, dus van de client.
"""

from gunicorn import glogging


class Toegangslog(glogging.Logger):
    def access(self, resp, req, environ, request_time):
        if not self.access_log_enabled:
            return
        # Ruw pad, niet PATH_INFO: gedecodeerde tekens als %0a kunnen geen eigen regel maken.
        pad = environ.get("RAW_URI", "").split("?", 1)[0]
        if pad.startswith("/health/") and "HTTP_X_FORWARDED_FOR" not in environ:
            return
        if pad.startswith("/uitnodiging/"):
            pad = "/uitnodiging/..."
        elif "%" in pad:
            pad = pad[:pad.index("%")] + "..."
        status = str(resp.status).split(None, 1)[0]
        self.access_log.info('%s %s "%s %s" %s %s', environ.get("REMOTE_ADDR", "-"), self.now(),
                             environ.get("REQUEST_METHOD", "-"), pad, status, resp.sent or 0)
