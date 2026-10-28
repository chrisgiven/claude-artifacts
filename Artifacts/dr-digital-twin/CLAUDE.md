# dr-digital-twin

DR digital twin platform. Read docs/ADR-001-platform-architecture.md before changing structure, and ROADMAP.md for what's next.

## Commands
- Tests: `python3 -m unittest discover -s tests -t .`
- Validate scenarios: `python3 -m drtwin validate`
- Full drill (needs Docker, about 6 min): `python3 -m drtwin run`
- Kill switch: `python3 -m drtwin teardown`
- Web console: `python3 -m drtwin console` (Portainer deploy: docs/PORTAINER.md)

## Rules
- Never weaken a gate. The isolation proof and drift check fail closed, before any fault.
- Providers never compute RTO/RPO. Only `drtwin/measure.py` does, from client records.
- New scenario actions go in the provider's `actions()` map, plus a test.
- Engine code stays stdlib + PyYAML.
- docker-compose.yml must stay free of bind mounts: the console runs compose through the host socket from inside a container.
