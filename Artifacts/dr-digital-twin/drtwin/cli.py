"""drtwin CLI.

    python3 -m drtwin list                         # scenarios and their targets
    python3 -m drtwin validate                     # schema-check every scenario
    python3 -m drtwin run                          # all scenarios
    python3 -m drtwin run dr-site-a-loss --declare-delay 60
    python3 -m drtwin teardown                     # kill switch + attestation
"""
import argparse
import json
import sys
from pathlib import Path

import yaml

from drtwin import evidence, scenario
from drtwin.engine import run_all
from drtwin.load import Client
from drtwin.providers import PROVIDERS

ROOT = Path(__file__).resolve().parent.parent


def setup(args):
    manifest = yaml.safe_load((ROOT / args.manifest).read_text())
    provider_name = args.provider or manifest["provider"]
    provider = PROVIDERS[provider_name](manifest, ROOT, **({"build": args.build} if hasattr(args, "build") else {}))
    args.provider = provider_name
    scenarios = scenario.load_dir(ROOT / "scenarios", provider.actions().keys())
    return manifest, provider, scenarios


def cmd_list(args):
    _, _, scenarios = setup(args)
    for s in scenarios.values():
        print(f"{s.id:28} {s.tier:6} RTO {s.targets['rto_s']:>4}s  RPO {s.targets['rpo_s']:>3}s  {s.title}")


def cmd_validate(args):
    _, _, scenarios = setup(args)  # raises ScenarioError on the first bad file
    print(f"{len(scenarios)} scenarios valid")


def cmd_run(args):
    manifest, provider, scenarios = setup(args)
    unknown = set(args.scenarios) - scenarios.keys()
    if unknown:
        sys.exit(f"unknown scenario(s): {', '.join(sorted(unknown))}")
    chosen = [scenarios[s] for s in (args.scenarios or scenarios)]
    client = Client(manifest["endpoint"], manifest.get("health_path", "/health"))
    results, errors, attestation = run_all(chosen, provider, client, args)
    out = evidence.write_pack(ROOT / "reports", results, errors, attestation, args)
    print(f"\nEvidence pack: {out}\nScorecard:     {out / 'scorecard.html'}\nTrend:         {ROOT / 'reports' / 'trend.html'}")
    if attestation is not None:
        print(f"Teardown:      {'verified' if attestation['destroyed'] else 'RESIDUAL OBJECTS — check results.json'}")
    sys.exit(1 if errors or not all(r["metrics"]["rto_pass"] and r["metrics"]["rpo_pass"] for r in results) else 0)


def cmd_teardown(args):
    _, provider, _ = setup(args)
    att = provider.teardown()
    print(json.dumps(att, indent=2))
    sys.exit(0 if att["destroyed"] else 1)


def main(argv=None):
    p = argparse.ArgumentParser(prog="drtwin", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--manifest", default="twin.yaml")
    p.add_argument("--provider", help="override the manifest's provider")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    sub.add_parser("validate").set_defaults(fn=cmd_validate)
    sub.add_parser("teardown").set_defaults(fn=cmd_teardown)
    r = sub.add_parser("run")
    r.add_argument("scenarios", nargs="*")
    r.add_argument("--rate", type=float, default=10, help="writes per second")
    r.add_argument("--declare-delay", type=float, default=15, help="simulated human decision time (s)")
    r.add_argument("--warmup", type=float, default=10)
    r.add_argument("--cooldown", type=float, default=10)
    r.add_argument("--build", action="store_true", help="rebuild the app image")
    r.add_argument("--keep", action="store_true", help="leave the twin running (no teardown)")
    r.set_defaults(fn=cmd_run)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
