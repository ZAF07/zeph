# Deployment guide

Zeph runs on one VPS (HostHatch, Debian 13) with the same `docker-compose.yml` and images as local (ADR-0005). Only `.env` differs.

In production, `COMPOSE_PROFILES=prod` adds **Caddy**, which serves the Dashboard and the backend over HTTPS on one domain and gets its certificate from Let's Encrypt by itself:

- `/api/*`, `/telegram/*` and `/health` go to the backend
- everything else goes to the Dashboard

ngrok and the eval-runner do not run in production. Postgres, backend and web publish their ports on `127.0.0.1` only, so from the internet only Caddy (80 and 443) answers. This matters because Docker bypasses `ufw`: a firewall rule alone would not hide them.

## First setup

Do these once, in order.

1. **Server.** Follow `.scratch/mvp/issues/archive/32-set-up-the-vps.md`: Docker Engine, the admin user `zaf`, the `deploy` user (Docker, no sudo), key-only SSH with root login off, `ufw` allowing 22/80/443, 4 GB swap. Then, as `zaf`, install `make` (used by `make restart`) and `cron` (runs the nightly backup):

   ```
   sudo apt install -y make cron
   ```

2. **Domain.** Follow `.scratch/mvp/issues/archive/33-free-domain-on-duckdns.md`, so the DuckDNS name points at the server.

3. **Backup storage.** Follow `.scratch/mvp/issues/archive/34-backup-storage-on-r2.md`: the `zeph-backups` R2 bucket with a 30-day delete rule, and an `r2` rclone remote for `deploy`. Install rclone from rclone.org, not with `apt`: Debian's rclone is too old for R2 and fails uploads with `501 Not Implemented`.

4. **Clone.** As `deploy`, clone only the `production` branch to `~/zeph` (issue 35 has the details, including the read-only deploy key):

   ```
   git clone -b production --single-branch git@github.com:ZAF07/zeph.git ~/zeph
   ```

5. **Production `.env`.** In `~/zeph`, run `cp .env.example .env` and fill it in. Different from local:

   ```
   COMPOSE_PROFILES=prod
   PORT_BIND_ADDRESS=127.0.0.1
   PRODUCTION_DOMAIN=zeph-beta.duckdns.org
   WEBHOOK_BASE_URL=https://zeph-beta.duckdns.org
   NEXT_PUBLIC_API_URL=https://zeph-beta.duckdns.org
   DASHBOARD_URL=https://zeph-beta.duckdns.org
   MODEL_CALL_DEVELOPER_LOGS=false
   NGROK_AUTHTOKEN=
   NGROK_DOMAIN=
   ```

   - `POSTGRES_PASSWORD` and `TELEGRAM_WEBHOOK_SECRET`: new strong values, made with `openssl rand -hex 32`. Never reuse local ones.
   - Clerk: the development keys for now. A Clerk production instance needs DNS records on a domain we own, which DuckDNS can't give.
   - `NEXT_PUBLIC_API_URL` is baked into the Dashboard when it is built. If you change it, rebuild (`docker compose up -d --build`).
   - `.env` never goes into git. App secrets live only in this file.
   - If `PRODUCTION_DOMAIN` is empty, Caddy won't start. Check `docker compose logs caddy` if the site doesn't load.

6. **Start.** In `~/zeph`:

   ```
   docker compose up -d --build
   ```

   The first build takes a while. Database migrations run when the backend starts, and the backend registers the Telegram webhook at `WEBHOOK_BASE_URL/telegram/webhook` with `TELEGRAM_WEBHOOK_SECRET`.

7. **Check.**

   - `docker compose ps`: postgres, backend, web and caddy are up; no ngrok or eval-runner.
   - `curl https://zeph-beta.duckdns.org/health` prints `{"status":"ok"}`.
   - Open `https://zeph-beta.duckdns.org`: the padlock shows and the Dashboard loads.
   - `curl https://api.telegram.org/bot<token>/getWebhookInfo` shows the DuckDNS URL and no `last_error_message`.
   - From your laptop, only 80 and 443 answer:

     ```
     for port in 80 443 3000 5432 8000; do nc -z -w 3 zeph-beta.duckdns.org $port && echo "$port open" || echo "$port closed"; done
     ```

     Expected: 80 and 443 open; 3000, 5432 and 8000 closed.

   - Sign up, connect Telegram and check the welcome message arrives.

8. **Nightly backup.** See [Backups](#backups).

Every service has `restart: unless-stopped`, so after `sudo reboot` or a Docker upgrade the app comes back by itself. Check once with `sudo reboot`, wait a minute, then `docker compose ps`.

## Updating by hand

As `deploy`, in `~/zeph`:

```
git pull
docker compose up -d --build
```

Changes go live by merging `main` into `production`. Issue 31 will run these two steps automatically on every push to `production`.

After changing only `.env`, run `make restart`: it rebuilds and recreates the containers so they read `.env` again. Plain `docker compose restart` does not.

## Backups

`scripts/backup.sh` dumps the database with `pg_dump` into `~/backups` and copies the dump to `r2:zeph-backups` with `rclone copy`. Local dumps are deleted after 7 days; the R2 bucket deletes its copies after 30 days. The database itself lives on the `postgres-data` Docker volume, which survives restarts, rebuilds and reboots.

**Install the nightly job** (once, as `deploy`). It runs at 03:30 server time (UTC):

```
(crontab -l 2>/dev/null; echo '30 3 * * * $HOME/zeph/scripts/backup.sh >> $HOME/backup.log 2>&1') | crontab -
crontab -l
```

**Run a backup now**, and see it in the bucket:

```
~/zeph/scripts/backup.sh
rclone ls r2:zeph-backups
```

Check `~/backup.log` if a night's backup is missing from the bucket.

**Restore** a backup (this replaces everything in the database). As `deploy`, in `~/zeph`:

```
rclone ls r2:zeph-backups
rclone copy r2:zeph-backups/zeph-<time>.dump ~/backups/
docker compose stop backend web
docker compose exec -T postgres sh -c 'pg_restore --clean --if-exists --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < ~/backups/zeph-<time>.dump
docker compose start backend web
```

`pg_restore` may print warnings such as "does not exist, skipping"; they are harmless. It worked if it ends without `errors ignored on restore`, and `curl https://<domain>/health` answers once the backend is back.

## Telegram bot token

Reset the bot token when it leaks or might have, not on a schedule. Steps: [RESET_TELEGRAM_TOKEN_GUIDE.md](RESET_TELEGRAM_TOKEN_GUIDE.md) (BotFather revoke → update `.env` → `make restart`).

## Local and production bots

Production keeps the real Telegram bot; local development uses its own bot, so the two stacks never take the webhook from each other. See [LOCAL_TELEGRAM_BOT_GUIDE.md](LOCAL_TELEGRAM_BOT_GUIDE.md) (ADR-0022).

## Changing the domain

The domain lives only in `.env`. To move to a new one:

1. Point the new domain's DNS at the server.
2. In `.env`, update `PRODUCTION_DOMAIN`, `WEBHOOK_BASE_URL`, `NEXT_PUBLIC_API_URL` and `DASHBOARD_URL`.
3. Run `docker compose up -d --build`. Caddy gets a certificate for the new name, and the backend registers the Telegram webhook at the new address when it starts.
