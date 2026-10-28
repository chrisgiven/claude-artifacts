"""Web console: start drills, watch progress, browse evidence packs.

    python3 -m drtwin console --port 8095

Runs one drill session at a time. It drives Docker through the host socket,
which is root-equivalent on that host: keep it on a trusted network and set
DRTWIN_CONSOLE_PASSWORD (HTTP basic auth, any username).
"""
import base64
import hmac
import html
import json
import os
import threading
import time
from argparse import Namespace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from drtwin import evidence
from drtwin.engine import run_all
from drtwin.load import Client

PASSWORD = os.environ.get("DRTWIN_CONSOLE_PASSWORD", "")


class Session:
    def __init__(self, setup, reports):
        self.setup, self.reports = setup, Path(reports)
        self.lock = threading.Lock()
        self.thread, self.log, self.state = None, [], "idle"

    def say(self, line):
        for part in str(line).strip("\n").splitlines():
            self.log.append(f"{time.strftime('%H:%M:%S')}  {part}")
        del self.log[:-400]

    def busy(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self, label, fn):
        with self.lock:
            if self.busy():
                return False
            self.log, self.state = [], label
            self.thread = threading.Thread(target=self._wrap, args=(fn,), daemon=True)
            self.thread.start()
            return True

    def _wrap(self, fn):
        try:
            fn()
        except Exception as e:
            self.say(f"ERROR: {type(e).__name__}: {e}")
        finally:
            self.state = "idle"

    def run(self, ids, declare_delay):
        def go():
            args = Namespace(manifest="twin.yaml", provider=None, build=False, rate=10.0,
                             declare_delay=declare_delay, warmup=10.0, cooldown=10.0, keep=False)
            manifest, provider, scenarios = self.setup(args)
            chosen = [scenarios[i] for i in ids if i in scenarios] or list(scenarios.values())
            client = Client(manifest["endpoint"], manifest.get("health_path", "/health"))
            self.say(f"Drill session: {', '.join(s.id for s in chosen)} (declare delay {declare_delay:.0f}s)")
            results, errors, att = run_all(chosen, provider, client, args, say=self.say)
            out = evidence.write_pack(self.reports, results, errors, att, args)
            self.say(f"Evidence pack written: {out.name}")
            if att is not None:
                self.say(f"Teardown: {'verified' if att['destroyed'] else 'RESIDUAL OBJECTS'}")
        return self.start("running drills", go)

    def teardown(self):
        def go():
            _, provider, _ = self.setup(Namespace(manifest="twin.yaml", provider=None))
            att = provider.teardown()
            self.say(f"Teardown: {'verified, nothing left' if att['destroyed'] else att['residual']}")
        return self.start("tearing down", go)

    def runs(self):
        if not self.reports.exists():
            return []
        out = []
        for d in sorted((p for p in self.reports.iterdir() if (p / "results.json").exists()), reverse=True)[:30]:
            try:
                data = json.loads((d / "results.json").read_text())
            except ValueError:
                continue
            res = data.get("results", [])
            passed = sum(r["metrics"]["rto_pass"] and r["metrics"]["rpo_pass"] for r in res)
            out.append({"run": d.name, "scenarios": len(res) + len(data.get("errors", [])),
                        "passed": passed, "aborted": len(data.get("errors", []))})
        return out


PAGE = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>DR Twin Console</title>
<style>%(css)s
.row{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start}.card{background:var(--card);border-radius:8px;padding:14px;flex:1 1 300px;min-width:0}
label{display:block;margin:4px 0}button{font:inherit;padding:6px 14px;border-radius:6px;border:1px solid var(--line);background:var(--bg);color:var(--fg);cursor:pointer}
button.primary{background:var(--ok);border-color:var(--ok);color:#fff}button:disabled{opacity:.5;cursor:default}
input[type=number]{width:70px;font:inherit;padding:3px 6px;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:4px}
pre{background:var(--card);padding:10px;border-radius:8px;max-height:360px;overflow:auto;font-size:12px;white-space:pre-wrap}
a{color:inherit}.state{font-weight:600}
</style></head><body>
<h1>DR Twin Console</h1>
<p class=muted>Twin <code>%(name)s</code> · provider %(provider)s · <a href="reports/trend.html">trend across runs</a></p>
<div class=row>
 <div class=card><h3 style="margin-top:0">Run drills</h3>
  %(checks)s
  <label>Declare delay (simulated human decision) <input id=delay type=number min=0 max=600 value=15> s</label>
  <p><button class=primary id=run>Run selected</button> <button id=down title="Destroy the twin and attest">Teardown</button></p>
 </div>
 <div class=card><h3 style="margin-top:0">Status: <span class=state id=state>…</span></h3><pre id=log>…</pre></div>
</div>
<h2>Evidence packs</h2>
<table><thead><tr><th>Run</th><th>Scenarios</th><th>Passed</th><th>Aborted</th><th></th></tr></thead><tbody id=runs></tbody></table>
<script>
const $=id=>document.getElementById(id);
async function post(path,body){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});
 if(!r.ok) alert((await r.json()).error||r.statusText); refresh();}
$('run').onclick=()=>post('api/run',{scenarios:[...document.querySelectorAll('input[name=sc]:checked')].map(c=>c.value),declare_delay:+$('delay').value});
$('down').onclick=()=>confirm('Destroy the twin and all its data?')&&post('api/teardown');
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
async function refresh(){
 try{const s=await (await fetch('api/status')).json();
  $('state').textContent=s.state;$('run').disabled=$('down').disabled=s.busy;
  const log=$('log'),atEnd=log.scrollTop+log.clientHeight>=log.scrollHeight-4;
  log.textContent=s.log.join('\\n')||'No activity yet.';if(atEnd)log.scrollTop=log.scrollHeight;
  $('runs').innerHTML=s.runs.map(r=>`<tr><td>${esc(r.run)}</td><td class=n>${r.scenarios}</td><td class=n>${r.passed}</td><td class=n>${r.aborted}</td>
   <td><a href="reports/${encodeURIComponent(r.run)}/scorecard.html" target=_blank>Scorecard</a> · <a href="reports/${encodeURIComponent(r.run)}/results.json" target=_blank>JSON</a></td></tr>`).join('')
   ||'<tr><td colspan=5 class=muted>No runs yet.</td></tr>';
 }catch(e){$('state').textContent='console unreachable'}}
refresh();setInterval(refresh,2000);
</script></body></html>"""


def make_handler(session, scenarios_meta, manifest):
    checks = "".join(
        f'<label><input type=checkbox name=sc value="{html.escape(s.id)}" checked> {html.escape(s.title)} '
        f'<span class=muted>(RTO {s.targets["rto_s"]}s · RPO {s.targets["rpo_s"]}s)</span></label>'
        for s in scenarios_meta.values())
    page = PAGE % {"css": evidence.CSS, "name": html.escape(manifest["name"]),
                   "provider": html.escape(manifest["provider"]), "checks": checks}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def authorized(self):
            if not PASSWORD:
                return True
            auth = self.headers.get("Authorization", "")
            if auth.startswith("Basic "):
                try:
                    _, _, pw = base64.b64decode(auth[6:]).decode().partition(":")
                    if hmac.compare_digest(pw, PASSWORD):
                        return True
                except ValueError:
                    pass
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="drtwin"')
            self.end_headers()
            return False

        def send(self, code, data, ctype="application/json"):
            data = data if isinstance(data, bytes) else json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if not self.authorized():
                return
            path = self.path.split("?")[0]
            if path == "/":
                return self.send(200, page.encode(), "text/html; charset=utf-8")
            if path == "/api/status":
                return self.send(200, {"state": session.state, "busy": session.busy(),
                                       "log": session.log[-200:], "runs": session.runs()})
            if path.startswith("/reports/"):
                base = session.reports.resolve()
                target = (base / path[len("/reports/"):]).resolve()
                if base in target.parents and target.is_file():
                    ctype = {".html": "text/html; charset=utf-8", ".json": "application/json"}.get(
                        target.suffix, "text/plain; charset=utf-8")
                    return self.send(200, target.read_bytes(), ctype)
            self.send(404, {"error": "not found"})

        def do_POST(self):
            if not self.authorized():
                return
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            except ValueError:
                return self.send(400, {"error": "bad JSON"})
            if self.path == "/api/run":
                delay = float(body.get("declare_delay", 15))
                if not 0 <= delay <= 600:
                    return self.send(400, {"error": "declare_delay must be 0-600"})
                ok = session.run([str(s) for s in body.get("scenarios", [])], delay)
            elif self.path == "/api/teardown":
                ok = session.teardown()
            else:
                return self.send(404, {"error": "not found"})
            self.send(202 if ok else 409, {"started": ok} if ok else {"error": "a session is already running"})

    return Handler


def serve(setup, reports, port):
    manifest, _, scenarios = setup(Namespace(manifest="twin.yaml", provider=None))
    session = Session(setup, reports)
    print(f"DR Twin Console on :{port}" + ("" if PASSWORD else "  (no password set)"), flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), make_handler(session, scenarios, manifest)).serve_forever()
