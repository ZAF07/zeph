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
2. **Let it log in as `deploy`:** append the public half on the VPS, using your own key to get in (password login is off):
   ```
   cat ~/.ssh/zeph_github_actions.pub | ssh zeph-deploy 'cat >> ~/.ssh/authorized_keys'
   ```
   Check: `ssh -i ~/.ssh/zeph_github_actions -o IdentitiesOnly=yes deploy@<server IP>` works.
3. **Add the GitHub secrets:** repo → **Settings → Secrets and variables → Actions → New repository secret**:
   - `SSH_KEY`: the whole private key (`cat ~/.ssh/zeph_github_actions`)
   - `SSH_HOST`: the VPS IP
   - `SSH_USER`: `deploy`
   - `SSH_KNOWN_HOSTS`: the server's host key, from `ssh-keyscan -t ed25519 <server IP>`
     Why the host key: the workflow checks it is talking to your server, not something pretending to be it.
4. Only these four. No app secrets go in GitHub; they stay in the server's `.env`.

## Acceptance criteria

- [x] The GitHub key logs in as `deploy`
- [x] The four secrets exist in the repo, and nothing else

## Blocked by

- `.scratch/mvp/issues/archive/32-set-up-the-vps.md`
