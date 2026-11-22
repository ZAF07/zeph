# 36 — GitHub secrets for auto deploy

Status: ready-for-human

## Parent

`.scratch/mvp/PRD.md`

## What to do

Give GitHub Actions its own key to log into the VPS, so pushes to `production` can deploy (issue 31).

1. **Make a key just for GitHub** on your laptop:
   ```
   ssh-keygen -t ed25519 -f ~/.ssh/zeph_github_actions -N "" -C "github-actions"
   ```
   Why a separate key: you can remove GitHub's access without touching your own login.
2. **Let it log in as `deploy`:** append the public half to the VPS:
   ```
   ssh-copy-id -i ~/.ssh/zeph_github_actions.pub deploy@<server IP>
   ```
   Check: `ssh -i ~/.ssh/zeph_github_actions deploy@<server IP>` works.
3. **Add the GitHub secrets:** repo → **Settings → Secrets and variables → Actions → New repository secret**:
   - `SSH_KEY`: the whole private key (`cat ~/.ssh/zeph_github_actions`)
   - `SSH_HOST`: the VPS IP
   - `SSH_USER`: `deploy`
4. Only these three. No app secrets go in GitHub; they stay in the server's `.env`.

## Acceptance criteria

- [ ] The GitHub key logs in as `deploy`
- [ ] The three secrets exist in the repo, and nothing else

## Blocked by

- `.scratch/mvp/issues/32-set-up-the-vps.md`
