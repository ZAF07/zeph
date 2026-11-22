# 33 — Free domain on DuckDNS

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to do

Get a free, fixed name for the server until Zeph has its real name and domain.

1. Go to https://www.duckdns.org and sign in (GitHub or Google).
2. Add a subdomain, e.g. `zeph-dev` → you get `zeph-dev.duckdns.org`.
3. In the **current ip** box, enter the VPS IP from issue 32 and click **update ip**.
4. Check from your laptop: `dig +short zeph-dev.duckdns.org` prints the VPS IP (can take a few minutes).

Why DuckDNS: the name never changes, and Caddy can get a real HTTPS certificate for it. Random-URL tunnels change on restart and would break the Telegram webhook and the Dashboard's API address (it is baked into the build).

Limit: a Clerk _production_ instance needs DNS records on a domain you own, which DuckDNS can't add. Keep Clerk's _development_ keys until the real domain exists.

## Acceptance criteria

- [x] `dig +short <name>.duckdns.org` returns the VPS IP
- [x] The name is written down (goes into the prod `.env` in issue 35)

## Blocked by

- `.scratch/mvp/issues/32-set-up-the-vps.md`

## Commits:

58ac79a
