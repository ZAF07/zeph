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
   PRODUCTION_DOMAIN=zeph-dev.duckdns.org
   WEBHOOK_BASE_URL=https://zeph-dev.duckdns.org
   NEXT_PUBLIC_API_URL=https://zeph-dev.duckdns.org
   DASHBOARD_URL=https://zeph-dev.duckdns.org
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
   - `curl https://zeph-dev.duckdns.org/health` prints `{"status":"ok"}`.
   - Open `https://zeph-dev.duckdns.org`: the padlock shows and the Dashboard loads.
   - `curl https://api.telegram.org/bot<token>/getWebhookInfo` shows the DuckDNS URL and no `last_error_message`.
   - From your laptop, only 80 and 443 answer:

     ```
     for port in 80 443 3000 5432 8000; do nc -z -w 3 zeph-dev.duckdns.org $port && echo "$port open" || echo "$port closed"; done
     ```

     Expected: 80 and 443 open; 3000, 5432 and 8000 closed.

   - Sign up, connect Telegram and check the welcome message arrives.

8. **Nightly backup.** See [Backups](#backups).

Every service has `restart: unless-stopped`, so after `sudo reboot` or a Docker upgrade the app comes back by itself. Check once with `sudo reboot`, wait a minute, then `docker compose ps`.

## Deploying on push

`main` is the everyday branch. A change goes live by merging `main` into `production` and pushing:

```
git checkout production && git pull
git merge main
git push origin production
```

Every push to `production` runs `.github/workflows/deploy.yml` (repo → **Actions → Deploy**):

1. **Checks:** `make check`. If any check fails, nothing is deployed.
2. **Deploy:** logs into the server as `deploy` over SSH and, in `~/zeph`, moves `production` forward to the commit that passed the checks (`git fetch` and `git merge --ff-only`), then runs `docker compose up -d --build`. The server builds the images itself, so build-time values like `NEXT_PUBLIC_API_URL` come from its own `.env`. Migrations run when the backend starts.
3. **Health check:** calls `/health` on the live domain (`PRODUCTION_URL` in the workflow) for up to about 2.5 minutes. If it never answers, the run fails.

Only one deploy runs at a time. A push made while a deploy is running waits for it to finish. If several pushes wait, only the newest one deploys; the ones in between are skipped. Each deploy brings a few seconds of downtime while containers restart.

If the build fails on the server, the running containers stay up on the old version.

**GitHub secrets** (repo → **Settings → Secrets and variables → Actions**). Issue 36 shows how to make them:

- `SSH_KEY`: the private key GitHub logs in with (`~/.ssh/zeph_github_actions`)
- `SSH_HOST`: the server's IP
- `SSH_USER`: `deploy`
- `SSH_KNOWN_HOSTS`: the server's host key (`ssh-keyscan -t ed25519 <server IP>`), so the workflow checks it is talking to the real server

Only these four. App secrets stay in the server's `.env`, never in GitHub or the repo.

**Roll back** to an older version:

- **Usual way:** undo the bad change on `main`, then send it live like any other change:

  ```
  git checkout main && git pull
  git revert <bad commit>
  git push origin main
  git checkout production && git pull && git merge main && git push origin production
  ```

  It deploys like any other push, checks included. To bring the change back later, `git revert` the revert commit on `main`.
- **Fast way, when it can't wait for the checks:** as `deploy`, in `~/zeph`:

  ```
  git log --oneline           # find the last good commit
  git reset --hard <good commit>
  docker compose up -d --build
  ```

  Then undo the bad change on `main` the usual way, so the next deploy doesn't put it back.

## Updating by hand

When GitHub Actions is down, run the same two steps as `deploy`, in `~/zeph`:

```
git pull --ff-only
docker compose up -d --build
```

After changing only `.env`, run `make restart`: it rebuilds and recreates the containers so they read `.env` again. Plain `docker compose restart` does not.

## Backups

`scripts/backup.sh` dumps the database with `pg_dump` into `~/backups` and copies the dump to `r2:zeph-backups` with `rclone copy`. Local dumps are deleted after 7 days; the R2 bucket deletes its copies after 30 days. The database itself lives on the `postgres-data` Docker volume, which survives restarts, rebuilds and reboots.

**Install the nightly job** (as `deploy`). It runs at 19:30 server time (UTC), which is 03:30 at UTC+8, when the app is quietest:

```
(crontab -l 2>/dev/null | grep -v 'scripts/backup.sh'; echo '30 19 * * * $HOME/zeph/scripts/backup.sh >> $HOME/backup.log 2>&1') | crontab - && crontab -l
```

It removes any existing backup job first, so running it again just replaces the job.

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

## OpenRouter keys

Model calls go through OpenRouter with our own provider keys (BYOK, ADR-0028). They must never spend OpenRouter credits. Set `OPENROUTER_API_KEY` in `.env`; `CHAT_MODEL_ADAPTER` defaults to `openrouter`.

Do these once in the OpenRouter account, and again for any provider key added later:

1. In the BYOK (integrations) settings, add each provider key (Anthropic, DeepSeek) and set its "Shared capacity fallback" to "Never use any other provider or key for this key's models".
2. In the privacy settings, allow providers that may train on inputs. DeepSeek is one, and without this OpenRouter refuses DeepSeek's own servers ("Paid model training violation").

Two things in the code keep calls on our own keys:

- Each call may only be answered by the model's maker (the part of the name before the "/"), because our keys are the makers' keys. A model its maker does not serve fails with an error. For DeepSeek, pick the dated names DeepSeek itself serves (`deepseek/deepseek-v4.1-flash-1017`, `deepseek/deepseek-v4-pro-0813`); the undated names are only served by other hosts. The Claude models Admins can pick (`anthropic/claude-haiku-5.5`, `anthropic/claude-sonnet-5.5`, `anthropic/claude-opus-5.5`, `anthropic/claude-fable-5.2`) are served by Anthropic under those names. Opus and Fable always think, so the thinking switch does nothing for them.
- If a reply was still paid with credits, the backend logs the warning "was paid with OpenRouter credits, not our own key". OpenRouter's activity page shows the same per call (BYOK or not).

To go back to direct DeepSeek, set `CHAT_MODEL_ADAPTER=deepseek` and `DEEPSEEK_API_KEY`, and run `make restart`.

## Local and production bots

Production keeps the real Telegram bot; local development uses its own bot, so the two stacks never take the webhook from each other. See [LOCAL_TELEGRAM_BOT_GUIDE.md](LOCAL_TELEGRAM_BOT_GUIDE.md) (ADR-0022).

## Changing the domain

The domain lives in `.env` and in `PRODUCTION_URL` in `.github/workflows/deploy.yml`. To move to a new one:

1. Point the new domain's DNS at the server.
2. In `.env`, update `PRODUCTION_DOMAIN`, `WEBHOOK_BASE_URL`, `NEXT_PUBLIC_API_URL` and `DASHBOARD_URL`.
3. In `.github/workflows/deploy.yml`, update `PRODUCTION_URL` so the health check calls the new domain.
4. Run `docker compose up -d --build`. Caddy gets a certificate for the new name, and the backend registers the Telegram webhook at the new address when it starts.
