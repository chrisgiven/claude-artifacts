"""Synthetic client: sequenced writes so every acknowledged write is accountable."""
import json
import threading
import time
import urllib.error
import urllib.request


class Client:
    def __init__(self, base, health_path="/health"):
        self.base, self.health_path = base.rstrip("/"), health_path

    def call(self, method, path, timeout=5):
        req = urllib.request.Request(self.base + path, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, {}
        except Exception:
            return 0, {}

    def healthy(self):
        return self.call("GET", self.health_path)[0] == 200

    def surviving_seqs(self):
        code, body = self.call("GET", "/orders/seqs", timeout=10)
        if code != 200:
            raise RuntimeError("could not read surviving orders after recovery")
        return set(body["seqs"])


class Load(threading.Thread):
    def __init__(self, client, rate):
        super().__init__(daemon=True)
        self.client, self.gap = client, 1.0 / rate
        self.records, self._stop, self.seq = [], threading.Event(), 0

    def run(self):
        while not self._stop.is_set():
            self.seq += 1
            t = time.time()
            # Longer than the LB's upstream timeout, so a slow-but-committed
            # write is not miscounted as a client-side failure.
            code, body = self.client.call("POST", f"/orders?seq={self.seq}", timeout=6)
            self.records.append({"seq": self.seq, "t": t, "ok": code == 200, "code": code,
                                 "site": body.get("site"), "lat_ms": round((time.time() - t) * 1000)})
            time.sleep(max(0, self.gap - (time.time() - t)))

    def stop(self):
        self._stop.set()
        self.join()
