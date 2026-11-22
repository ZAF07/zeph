# 32 — Set up the VPS

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to do

Rent the server and make it safe and ready to run Docker. Commands are for Debian 13; Ubuntu 24.04 is the same except step 5 is already done.

1. **Order** HostHatch NVMe 16 GB (4 cores, 2 dedicated), OS Debian 13, in the location closest to you. Hostname: `zeph-prod-01`. One IPv4, IPv6 off. Add your Zeph SSH public key (`pbcopy < ~/.ssh/zeph.pub`; make it with `ssh-keygen -t ed25519 -f ~/.ssh/zeph -C "zeph-prod"`).
   Why the key: you log in with it, never with a password.
2. **Log in as root** from your laptop: `ssh -i ~/.ssh/zeph root@<server IP>` (the IP is in the HostHatch panel).
3. **Create your admin user** (it can use `sudo`) and give it your key:
   ```
   apt update && apt install -y sudo
   adduser zaf
   usermod -aG sudo zaf
   mkdir -p /home/zaf/.ssh
   cp ~/.ssh/authorized_keys /home/zaf/.ssh/
   chown -R zaf:zaf /home/zaf/.ssh
   chmod 700 /home/zaf/.ssh && chmod 600 /home/zaf/.ssh/authorized_keys
   ```
   In a new terminal, check `ssh -i ~/.ssh/zeph zaf@<server IP>` then `sudo whoami` prints `root`. From here on, work as `zaf`, not root.
   Why: step 8 turns off root login, so you need your own admin user first. Two users with different jobs: `zaf` runs admin commands, `deploy` (step 7) only runs the app.
4. **Update everything**, then reboot:
   ```
   sudo apt update && sudo apt upgrade -y
   sudo reboot
   ```
5. **Automatic security updates** (one-time setup; it then runs daily by itself):
   ```
   sudo apt install -y unattended-upgrades
   sudo dpkg-reconfigure -plow unattended-upgrades   # answer Yes
   ```
   It does not reboot for you. Reboot by hand now and then (`sudo reboot`).
6. **Install Docker Engine** from Docker's own repo, following https://docs.docker.com/engine/install/debian/ ("Install using the apt repository"). Check: `sudo docker run hello-world`.
   Why not `apt install docker.io`: Debian's package is older and lacks the `docker compose` plugin.
7. **Create the `deploy` user** and let it run Docker:
   ```
   sudo adduser deploy
   sudo usermod -aG docker deploy
   sudo mkdir -p /home/deploy/.ssh
   sudo cp ~/.ssh/authorized_keys /home/deploy/.ssh/
   sudo chown -R deploy:deploy /home/deploy/.ssh
   sudo chmod 700 /home/deploy/.ssh && sudo chmod 600 /home/deploy/.ssh/authorized_keys
   ```
   Check from your laptop: `ssh deploy@<server IP>` then `docker ps`.
   Why: the app and GitHub's deploys run as this user, not as an admin. If GitHub's key ever leaks, it can't run admin commands (`sudo`).
8. **Lock down SSH** (as `zaf`). Put the settings in their own file, so files the host added in `/etc/ssh/sshd_config.d/` can't override them:
   ```
   echo -e "PasswordAuthentication no\nPermitRootLogin no" | sudo tee /etc/ssh/sshd_config.d/00-zeph.conf
   sudo sshd -t && sudo systemctl restart ssh
   sudo sshd -T | grep -iE "passwordauthentication|permitrootlogin"   # both must say no
   ```
   **Keep your current session open** and, in a new terminal, check `ssh zeph` (as `zaf`) works and `ssh root@<server IP>` is refused.
   Why: bots try passwords and the `root` user on every public server all day. After this, only your keys get in, and never as root.
9. **Firewall** (allow 22 first, or you lock yourself out):
   ```
   sudo apt install -y ufw
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```
   80 and 443 are for Caddy (80 is also how Let's Encrypt checks the domain before giving a certificate).
10. **Swap (4 GB):**

```
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Check: `free -h` shows 4 GB swap.
Why: building the Dashboard uses a lot of memory for a short time while Postgres and the app still run. Without swap, Linux kills a process (maybe Postgres) when memory runs out.

## Acceptance criteria

- [x] `ssh zaf@<server IP>` (admin) and `ssh deploy@<server IP>` work with your key; password login and root login are refused
- [x] `docker ps` works as `deploy` without `sudo`
- [x] `sudo ufw status` shows only 22, 80, 443 allowed
- [x] `free -h` shows swap
- [x] Unattended-upgrades is enabled
- [x] Server IP written down (needed by issue 33)

## Blocked by

None

## Commits

0654d4b
