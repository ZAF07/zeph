# 34 — Backup storage on Cloudflare R2

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to do

Make a place off the server for the nightly database backups, and let the server upload to it.

Why off the server: if the VPS dies or is wiped, backups on it die too.
Why R2: free at this size (10 GB), and downloading a backup to restore it costs nothing.

**In Cloudflare:**

1. Sign up at https://dash.cloudflare.com and open **R2**. It asks for a payment card even on the free plan.
2. **Create bucket**: name `zeph-backups`.
3. In the bucket's **Settings → Object lifecycle rules**, add a rule: delete objects after 30 days.
   Why: old backups don't pile up forever.
4. **R2 → Manage API tokens → Create API token**: permission _Object Read & Write_, only for `zeph-backups`. Copy the **Access Key ID**, **Secret Access Key** and the **endpoint** (`https://<account id>.r2.cloudflarestorage.com`). The secret is shown only once.

**On the VPS (as `deploy`):**

5. Install the current rclone (as `zaf`; Debian's packaged rclone is too old for R2 and fails uploads with `501 Not Implemented`):
   ```
   sudo apt install -y unzip
   curl -fsSL https://rclone.org/install.sh | sudo bash
   ```
6. Run `rclone config` and add a remote:
   - name: `r2`
   - storage: `s3`, provider: `Cloudflare`
   - access key and secret from step 4
   - endpoint from step 4
   - leave the rest as default
   - then: `rclone config update r2 no_check_bucket true` (the token can only reach this bucket, so rclone must not try to check or create buckets)
7. Check it works:
   ```
   echo test > /tmp/test.txt
   rclone copy /tmp/test.txt r2:zeph-backups/
   rclone ls r2:zeph-backups
   rclone delete r2:zeph-backups/test.txt
   ```
8. Once issue 16 lands, add the nightly backup cron job exactly as its deployment guide says.

## Acceptance criteria

- [x] Bucket exists with a 30-day delete rule
- [x] The API token only reaches `zeph-backups`
- [x] `rclone ls r2:zeph-backups` works on the VPS as `deploy`
- [x] Nightly backup cron installed and one backup seen in the bucket the next day

## Blocked by

- `.scratch/mvp/issues/archive/32-set-up-the-vps.md`
- `.scratch/mvp/issues/archive/16-production-deployment.md` (step 8 only)

## Comments:

Last acceptance criteria cannot be checked until `.scratch/mvp/issues/16-production-deployment.md` is complete. It needs to add the backup cron job. Plese come back to this when `.scratch/mvp/issues/16-production-deployment.md` has added the backup cron job.

- 2026-11-22: Step 8 done. Issue 16 added `scripts/backup.sh` and the cron line in `docs/DEPLOYMENT_GUIDE.md`. The owner installed `make` and `cron`, then installed the job as `deploy`. A test run (set a minute ahead) put a dump in `r2:zeph-backups`; the job is back on 19:30 UTC (03:30 at UTC+8).
- 2026-11-22: Checked on the VPS during issue 31: `crontab -l` as `deploy` shows `30 19 * * * $HOME/zeph/scripts/backup.sh >> $HOME/backup.log 2>&1`, `~/backup.log` ends with `backed up zeph-2026-11-22T092201Z.dump`, and `rclone lsl r2:zeph-backups` lists that dump. Nothing left to do here.

## Completion

- Completed: 2026-11-22

## Commits:

`b7a6e23d11f297334ece35edb98aedb507a85dac` - partially completed issue
`7429bf2` - Production deployment: Caddy under prod profile, eval-runner under eval, ports on 127.0.0.1, restart policies, nightly R2 backup script and deployment guide (issue 16)
`cddc852` - Deployment guide: one cron command that replaces the backup job
`6696274` - Archive issues 16 and 34: production deployment and nightly R2 backup done
