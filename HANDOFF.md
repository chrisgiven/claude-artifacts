# Handoff

## Current goal

Shipped: live service health board on the hub (v1.2.0, 2026-07-27). Nothing in flight.

## Decisions made (and why)

- **Service list lives outside this repo.** `claude-artifacts` is public. A full host-and-port map of the private network does not belong in it, so `index.html` carries only the machinery and the list loads from `/services.json` at runtime. That file is gitignored and deployed only to the NAS.
- **`services.json` sits at `/volume1/Web/projects/services.json`, not inside the `claude-artifacts/` clone.** `sync-artifacts.sh` runs `git reset --hard origin/main` on the NAS clone; anything inside it would be destroyed. At the doc root it survives, and nginx still serves it at `/services.json`.
- **Probes use `mode:'no-cors'`, so the result proves the port answered, not what it said.** A 401 counts as up — correct for CouchDB, ObsidianRemote, and Plex. `credentials:'omit'` stops the browser negotiating Basic auth against the two that send `WWW-Authenticate`. Plex is probed at `/identity`, which answers 200 unauthenticated.
- **The nav item is hidden below 640px.** The nav has no wrap or scroll, so a fifth item pushed the page 56px wide on mobile. The section is still reachable by scrolling.

## Open questions

- Lab cards still hardcode `NAS-ADDR` (lines ~537/586/607) and are already public. Left alone deliberately — they predate this work — but if the LAN IP should not be public at all, they need addressing too.
- The board checks HTTP reachability, not container health. A container stuck in a restart loop could answer between probes and read green. Container state needs `docker ps` parsing, which belongs in `nas-health`, not a browser.

## Next step

To add or move a service, edit `services.json` on the NAS — no commit, no push, no HTML change:

```bash
scp -i ~/.ssh/id_nas NAS-USER@NAS-ADDR:/volume1/Web/projects/services.json .
# edit, then copy it back to the same path
```
