# Handoff

## Current goal

Shipped: LAN addresses removed from the tracked tree (v1.3.0, 2026-08-07). Nothing in flight.

## Decisions made (and why)

- **Service list lives outside this repo.** `claude-artifacts` is public. A full host-and-port map of the private network does not belong in it, so `index.html` carries only the machinery and the list loads from `/services.json` at runtime. That file is gitignored and deployed only to the NAS.
- **`services.json` sits at `/volume1/Web/projects/services.json`, not inside the `claude-artifacts/` clone.** `sync-artifacts.sh` runs `git reset --hard origin/main` on the NAS clone; anything inside it would be destroyed. At the doc root it survives, and nginx still serves it at `/services.json`.
- **Probes use `mode:'no-cors'`, so the result proves the port answered, not what it said.** A 401 counts as up — correct for CouchDB, ObsidianRemote, and Plex. `credentials:'omit'` stops the browser negotiating Basic auth against the two that send `WWW-Authenticate`. Plex is probed at `/identity`, which answers 200 unauthenticated.
- **The nav item is hidden below 640px.** The nav has no wrap or scroll, so a fifth item pushed the page 56px wide on mobile. The section is still reachable by scrolling.

- **Every Lab card with a private address now uses `data-svc-link`.** Sonos, Groundwork, AgentOS and Lights joined Vaultwarden and Tripwire on the runtime-injection pattern, so the tracked tree carries no LAN address. The `localhost` cards (AI Sound Engineer, BCDR, Switchboard) were left alone — `localhost` reveals nothing about the network and those genuinely run on the Mac, not the NAS.
- **The NAS target in `sync-artifacts.sh` moved out of the repo** to `~/.config/claude-artifacts/nas-host` (one line, `user@host`), overridable with `NAS_HOST`. If that file is missing the script still syncs and pushes, then warns and lets the NAS's own cron catch up — the same degradation as an unreachable NAS.

- **The git history was rewritten on 2026-08-07** to purge those addresses from all 54 commits, so a working-tree grep and a full-history grep now agree. Backup bundle of the pre-rewrite history was taken before the force-push.

## Open questions

- **The orphaned pre-rewrite commits are still on GitHub.** Force-pushing unreferenced them but does not delete them; they remain reachable by direct SHA (old tip `caf77e5`) until GitHub garbage-collects. Only a GitHub Support request expunges them. Left as-is — the scrubbed values are RFC1918 addresses plus a Tailscale name that still requires being on the tailnet.
- `services.json` lists AgentOS on the Mac mini, while the old hub card pointed at port 5599 on the NAS instead. Both were down when checked on 2026-08-07, so the `links.agentos` entry follows `services.json`. Confirm once AgentOS is running.
- The board checks HTTP reachability, not container health. A container stuck in a restart loop could answer between probes and read green. Container state needs `docker ps` parsing, which belongs in `nas-health`, not a browser.

## Next step

To add or move a service, edit `services.json` on the NAS — no commit, no push, no HTML change:

```bash
scp -i ~/.ssh/id_nas "$(cat ~/.config/claude-artifacts/nas-host)":/volume1/Web/projects/services.json .
# edit, then copy it back to the same path
```

Adding a Lab card whose URL is private: give the `<a class="card">` no `href`, add
`data-svc-link="<key>"`, and put the real URL under `links` in `services.json` on the
NAS. Never commit that file.
