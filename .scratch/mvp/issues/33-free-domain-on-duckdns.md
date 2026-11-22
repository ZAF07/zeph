# 33 — Free domain on DuckDNS

Status: ready-for-human

## Parent

`.scratch/mvp/PRD.md`

## What to do

Get a free, fixed name for the server until Zeph has its real name and domain.

1. Go to https://www.duckdns.org and sign in (GitHub or Google).
2. Add a subdomain, e.g. `zeph-beta` → you get `zeph-beta.duckdns.org`.
3. In the **current ip** box, enter the VPS IP from issue 32 and click **update ip**.
4. Check from your laptop: `dig +short zeph-beta.duckdns.org` prints the VPS IP (can take a few minutes).

Why DuckDNS: the name never changes, and Caddy can get a real HTTPS certificate for it. Random-URL tunnels change on restart and would break the Telegram webhook and the Dashboard's API address (it is baked into the build).

Limit: a Clerk *production* instance needs DNS records on a domain you own, which DuckDNS can't add. Keep Clerk's *development* keys until the real domain exists.

## Acceptance criteria

- [ ] `dig +short <name>.duckdns.org` returns the VPS IP
- [ ] The name is written down (goes into the prod `.env` in issue 35)

## Blocked by

- `.scratch/mvp/issues/32-set-up-the-vps.md`
