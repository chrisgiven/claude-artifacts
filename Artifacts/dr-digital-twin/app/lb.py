"""Global load balancer (GSLB stand-in) with active health checks.

Routes to healthy primary-site nodes; falls back to the DR-site pool only
when no primary node is healthy, like an HAProxy `backup` server.
"""
import json
import os
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PRIMARY = os.environ["PRIMARY_POOL"].split(",")
BACKUP = os.environ.get("BACKUP_POOL", "").split(",") if os.environ.get("BACKUP_POOL") else []
INTERVAL = float(os.environ.get("CHECK_INTERVAL", "1"))
FALL, RISE = 2, 2

state = {b: {"up": False, "fails": 0, "oks": 0} for b in PRIMARY + BACKUP}
lock = threading.Lock()
rr = 0


def check(backend):
    try:
        # Longer than one dead-host DNS lookup (~2s), so a backend that is slow
        # but working after a failover is not flapped out of the pool.
        with urllib.request.urlopen(f"http://{backend}/health", timeout=4) as r:
            return r.status == 200
    except Exception:
        return False


def health_loop(b):
    while True:
        ok = check(b)
        with lock:
            s = state[b]
            if ok:
                s["oks"], s["fails"] = s["oks"] + 1, 0
                if s["oks"] >= RISE:
                    s["up"] = True
            else:
                s["fails"], s["oks"] = s["fails"] + 1, 0
                if s["fails"] >= FALL:
                    s["up"] = False
        time.sleep(INTERVAL)


def candidates():
    global rr
    with lock:
        live = [b for b in PRIMARY if state[b]["up"]] or [b for b in BACKUP if state[b]["up"]]
        rr += 1
    return live[rr % len(live):] + live[: rr % len(live)] if live else []


class Proxy(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, code, data, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def forward(self, method):
        if self.path == "/lb/status":
            with lock:
                return self.send(200, json.dumps(state).encode())
        backends = candidates()
        if not backends:
            return self.send(503, b'{"error":"no healthy backend"}')
        # Retry the next backend only on connection failure: a backend that
        # answered (even 5xx) may have committed the write.
        for b in backends:
            req = urllib.request.Request(f"http://{b}{self.path}", method=method)
            try:
                with urllib.request.urlopen(req, timeout=5) as r:
                    return self.send(r.status, r.read())
            except urllib.error.HTTPError as e:
                return self.send(e.code, e.read())
            except Exception:
                continue
        self.send(502, b'{"error":"all backends failed"}')

    def do_GET(self):
        self.forward("GET")

    def do_POST(self):
        self.forward("POST")


if __name__ == "__main__":
    for b in state:
        threading.Thread(target=health_loop, args=(b,), daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", 8080), Proxy).serve_forever()
