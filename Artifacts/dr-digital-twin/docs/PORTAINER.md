# Deploy on Portainer

The stack runs one container: the **DR Twin Console** (web UI and drill engine). When you start a drill, the console creates the twin (`drtwin-*` containers) on the same Docker host, runs the scenarios, writes the evidence pack and tears the twin down.

## One-time: make the images pullable
GitHub Actions (`.github/workflows/drtwin-images.yml`) publishes three amd64/arm64 images to GHCR: `drtwin-console`, `drtwin-app` and `drtwin-db`. New GHCR packages are **private**. Either:
- **Public (simplest):** github.com → your profile → Packages → each `drtwin-*` package → Package settings → Change visibility → Public. Or
- **Private:** in Portainer go to Registries → Add registry → Custom, URL `ghcr.io`, with a GitHub token that has `read:packages`.

## Deploy
1. Portainer → Stacks → Add stack, name it `drtwin-console`.
2. Web editor → paste `portainer-stack.yml`.
3. Environment variables:

| Name | Value |
|---|---|
| `DRTWIN_CONSOLE_PASSWORD` | Required. Any username works at the login prompt |
| `CONSOLE_PORT` | Optional, default `8095` |
| `TWIN_PORT` | Optional, default `18080` (twin LB, bound to 127.0.0.1) |

4. Deploy, then open `http://<docker-host>:8095`.

## Use
- Choose scenarios, set the declare delay, then click **Run selected**. A full set takes about 6 min. The log updates live.
- Each run adds a row under **Evidence packs** with links to the scorecard and JSON. **Trend across runs** compares runs over time.
- **Teardown** is the kill switch. It destroys any twin left running and verifies nothing remains.

## Notes
- Reports persist in the `reports` volume, so they survive console updates.
- To update, re-pull the image in Portainer (Stack → Update → "Re-pull image").
- Twin containers aren't part of the stack. Portainer shows them as project `drtwin` while a drill runs; they're removed afterwards.
- Resources: the twin uses about 7 small containers, roughly 600 MB RAM, during a drill.
