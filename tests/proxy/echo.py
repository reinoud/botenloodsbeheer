"""Upstream voor tests/proxy/padproeven.sh: geeft als JSON het pad terug dat Traefik doorstuurde."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Echo(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def antwoord(self):
        lichaam = json.dumps({"pad": self.path}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(lichaam)))
        self.end_headers()
        self.wfile.write(lichaam)

    do_GET = do_POST = antwoord

    def log_message(self, *args):
        pass


ThreadingHTTPServer(("", 8000), Echo).serve_forever()
