"""Order service: the 'production workload' inside the twin.

Every write carries a client sequence number so the harness can prove
exactly which acknowledged writes survived a recovery (measured RPO).
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import psycopg

SITE = os.environ.get("SITE", "?")
NODE = os.environ.get("NODE", "?")
# libpq tries each host in order and only accepts a writable primary, so the
# app follows a promotion without a config change.
DSN = os.environ["DB_DSN"]


def db():
    return psycopg.connect(DSN, autocommit=True, connect_timeout=2)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            with db() as conn:
                if path == "/health":
                    # Functional check: touches the business table, not just `SELECT 1`.
                    conn.execute("SELECT 1 FROM orders LIMIT 1")
                    return self.reply(200, {"ok": True, "site": SITE, "node": NODE})
                if path == "/orders/seqs":
                    rows = conn.execute("SELECT client_seq FROM orders").fetchall()
                    return self.reply(200, {"seqs": [r[0] for r in rows]})
        except Exception as e:
            return self.reply(503, {"ok": False, "error": str(e)[:200], "node": NODE})
        self.reply(404, {"error": "not found"})

    def do_POST(self):
        url = urlparse(self.path)
        if url.path != "/orders":
            return self.reply(404, {"error": "not found"})
        seq = int(parse_qs(url.query)["seq"][0])
        try:
            with db() as conn:
                conn.execute(
                    "INSERT INTO orders (client_seq, site, node) VALUES (%s, %s, %s)",
                    (seq, SITE, NODE),
                )
            self.reply(200, {"seq": seq, "site": SITE, "node": NODE})
        except Exception as e:
            self.reply(503, {"error": str(e)[:200], "node": NODE})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
