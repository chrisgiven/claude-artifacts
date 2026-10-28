"""Reference provider: the two-site twin in docker-compose.yml on local Docker."""
import json
import subprocess
import time

from drtwin.providers.base import Provider
from drtwin.util import wait_for

ISOLATION_PROBE = """
import json, socket
checks = []
for host, port in [("1.1.1.1", 443), ("8.8.8.8", 53)]:
    s = socket.socket(); s.settimeout(3)
    try:
        s.connect((host, port)); checks.append({"check": f"egress {host}:{port}", "passed": False})
    except OSError:
        checks.append({"check": f"egress {host}:{port}", "passed": True})
try:
    socket.gethostbyname("example.com"); checks.append({"check": "external DNS", "passed": False})
except OSError:
    checks.append({"check": "external DNS", "passed": True})
print(json.dumps(checks))
"""


class DockerProvider(Provider):
    name = "docker"

    def __init__(self, manifest, root, build=False):
        super().__init__(manifest, root)
        self.build = build
        self.project = "drtwin"

    # ------------------------------------------------------------ plumbing

    def compose(self, *args, check=True, timeout=180):
        r = subprocess.run(["docker", "compose", "-f", self.manifest["compose_file"], *args],
                           cwd=self.root, capture_output=True, text=True, timeout=timeout)
        if check and r.returncode != 0:
            raise RuntimeError(f"docker compose {' '.join(args)}: {r.stderr.strip()}")
        return r

    def psql(self, service, sql):
        return self.compose("exec", "-T", service, "psql", "-U", "postgres", "-d", "orders",
                            "-tAc", sql).stdout.strip()

    def vault(self):
        names = self.compose("exec", "-T", "backup", "ls", "/vault").stdout.split()
        return sorted(int(n[7:-5]) for n in names if n.startswith("orders-") and n.endswith(".dump"))

    # ------------------------------------------------------------ lifecycle

    def up(self, healthy):
        self.compose("down", "-v", "--remove-orphans", check=False)
        self.compose("up", "-d", *(["--build"] if self.build else []), timeout=600)
        wait_for("LB healthy", healthy, timeout=120)
        primary = self.manifest["expected"]["replication"]["primary"]
        wait_for("standby streaming", lambda: self.psql(
            primary, "SELECT count(*) FROM pg_stat_replication WHERE state='streaming'") == "1")
        wait_for("first backup in vault", lambda: bool(self.vault()), timeout=90)

    def isolation_proof(self):
        r = self.compose("exec", "-T", "app-a1", "python", "-c", ISOLATION_PROBE, check=False)
        try:
            checks = json.loads(r.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            checks = [{"check": "probe ran", "passed": False, "detail": r.stderr.strip()[:200]}]
        return {"passed": all(c["passed"] for c in checks), "checks": checks,
                "probed_from": "app-a1"}

    def inventory(self):
        rows = self.compose("ps", "--format", "json").stdout.strip()
        # Compose prints one JSON object per line (newer) or one array (older).
        items = json.loads(rows) if rows.startswith("[") else [json.loads(l) for l in rows.splitlines() if l]
        services = {i["Service"]: {"state": i["State"], "image": i["Image"]} for i in items}
        primary = self.manifest["expected"]["replication"]["primary"]
        standbys = int(self.psql(primary, "SELECT count(*) FROM pg_stat_replication WHERE state='streaming'"))
        stamps = self.vault()
        return {"services": services, "replication_standbys": standbys,
                "backup_age_s": round(time.time() - stamps[-1], 1) if stamps else None}

    def teardown(self):
        self.compose("down", "-v", "--remove-orphans", check=False)
        label = f"label=com.docker.compose.project={self.project}"
        residual = {
            kind: subprocess.run(["docker", kind, "ls", *(["-a"] if kind == "container" else []),
                                  "-q", "--filter", label],
                                 capture_output=True, text=True).stdout.split()
            for kind in ("container", "volume", "network")}
        return {"project": self.project, "verified_at": time.time(),
                "residual": residual, "destroyed": not any(residual.values())}

    # ------------------------------------------------------------ actions

    def actions(self):
        return {
            "kill": lambda a, ctx: self.compose("kill", *a["services"]) and None,
            "stop": lambda a, ctx: self.compose("stop", "-t", "2", *a["services"]) and None,
            "start": lambda a, ctx: self.compose("start", *a["services"]) and None,
            "sql": lambda a, ctx: self.psql(a["service"], a["statement"]) and None,
            "promote": self._promote,
            "declare": self._declare,
            "wait_healthy": lambda a, ctx: wait_for("service healthy via LB", ctx["healthy"],
                                                    timeout=a.get("timeout_s", 180)),
            "find_clean_backup": self._find_clean_backup,
            "restore_backup": self._restore_backup,
        }

    def _promote(self, a, ctx):
        self.psql(a["service"], "SELECT pg_promote(true, 60)")
        return f"{a['service']} promoted to primary"

    def _declare(self, a, ctx):
        delay = a.get("delay_s", ctx["declare_delay"])
        time.sleep(delay)
        return f"simulated decision time {delay:.0f}s"

    def _find_clean_backup(self, a, ctx):
        clean = [s for s in self.vault() if s < ctx["t0"]]
        if not clean:
            raise RuntimeError("no backup older than the incident: unrecoverable")
        ctx["restore_point"] = clean[-1]
        return f"orders-{clean[-1]}.dump ({ctx['t0'] - clean[-1]:.0f}s before incident)"

    def _restore_backup(self, a, ctx):
        self.compose("exec", "-T", "backup", "pg_restore", "--clean", "--if-exists",
                     "-d", f"host={a['service']} dbname=orders user=postgres",
                     f"/vault/orders-{ctx['restore_point']}.dump")
        return f"restored orders-{ctx['restore_point']}.dump to {a['service']}"
