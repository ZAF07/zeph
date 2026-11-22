# 34 — Backup storage on Cloudflare R2

Status: ready-for-agent

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

5. Install rclone: `sudo apt install -y rclone`.
6. Run `rclone config` and add a remote:
   - name: `r2`
   - storage: `s3`, provider: `Cloudflare`
   - access key and secret from step 4
   - endpoint from step 4
   - leave the rest as default
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
- [ ] Nightly backup cron installed and one backup seen in the bucket the next day

## Blocked by

- `.scratch/mvp/issues/32-set-up-the-vps.md`
- `.scratch/mvp/issues/16-production-deployment.md` (step 8 only)

## Comments:

Last acceptance criteria cannot be checked until `.scratch/mvp/issues/16-production-deployment.md` is complete. Plese come back to this when `.scratch/mvp/issues/16-production-deployment.md` is complete.
