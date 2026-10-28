import tempfile
import textwrap
import unittest
from pathlib import Path

from drtwin import drift, scenario
from drtwin.evidence import strip_svg

ROOT = Path(__file__).resolve().parent.parent
ACTIONS = {"kill", "stop", "start", "sql", "promote", "declare", "wait_healthy",
           "find_clean_backup", "restore_backup"}


class Scenarios(unittest.TestCase):
    def test_shipped_scenarios_are_valid(self):
        s = scenario.load_dir(ROOT / "scenarios", ACTIONS)
        self.assertEqual(len(s), 4)
        self.assertEqual(s["dr-site-a-loss"].fault[0].args["services"], ["app-a1", "app-a2", "pg-a"])
        self.assertEqual(s["ha-db-primary"].runbook[0].actor, "human")

    def write(self, body):
        f = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
        f.write(textwrap.dedent(body))
        f.close()
        return f.name

    def test_unknown_action_rejected(self):
        p = self.write("""
            id: x
            title: x
            tier: HA
            targets: {rto_s: 1, rpo_s: 0}
            fault: [{name: f, action: explode}]
            runbook: [{name: r, action: wait_healthy}]
        """)
        with self.assertRaisesRegex(scenario.ScenarioError, "unknown action 'explode'"):
            scenario.load(p, ACTIONS)

    def test_missing_targets_rejected(self):
        p = self.write("""
            id: x
            title: x
            tier: HA
            fault: [{name: f, action: kill, services: [a]}]
            runbook: [{name: r, action: wait_healthy}]
        """)
        with self.assertRaisesRegex(scenario.ScenarioError, "missing targets"):
            scenario.load(p, ACTIONS)


class Drift(unittest.TestCase):
    expected = {"services": {"a": {}, "b": {}}, "replication": {"standbys": 1}, "backup": {"max_age_s": 60}}

    def obs(self, **kw):
        o = {"services": {"a": {"state": "running", "image": "i"}, "b": {"state": "running", "image": "i"}},
             "replication_standbys": 1, "backup_age_s": 10}
        o.update(kw)
        return o

    def test_clean_twin_passes(self):
        self.assertTrue(drift.check(self.expected, self.obs())["passed"])

    def test_missing_service_stale_backup_and_broken_replication_fail(self):
        r = drift.check(self.expected, self.obs(
            services={"a": {"state": "running", "image": "i"}}, replication_standbys=0, backup_age_s=600))
        failed = {c["check"] for c in r["checks"] if not c["passed"]}
        self.assertFalse(r["passed"])
        self.assertEqual(len(failed), 3)


class Evidence(unittest.TestCase):
    def test_timeline_runs_are_merged(self):
        tl = [{"t": i / 10, "ok": i < 50 or i > 80} for i in range(200)]
        self.assertEqual(strip_svg(tl).count("<rect"), 3)


if __name__ == "__main__":
    unittest.main()
