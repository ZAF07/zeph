# 32 — Set up the VPS

Status: ready-for-human

## Parent

`.scratch/mvp/PRD.md`

## What to do

Rent the server and make it safe and ready to run Docker. Commands are for Debian 13; Ubuntu 24.04 is the same except step 4 is already done.

1. **Order** OVHcloud VPS-2 (4 vCores, 8 GB RAM), OS Debian 13, in the data centre closest to you. Add your laptop's SSH public key (`cat ~/.ssh/id_ed25519.pub`) when ordering.
   Why the key: you log in with it, never with a password.
2. **Log in** from your laptop: `ssh debian@<server IP>` (the IP is in the OVH panel; the default user name is in OVH's email).
3. **Update everything**, then reboot:
   ```
   sudo apt update && sudo apt upgrade -y
   sudo reboot
   ```
4. **Automatic security updates** (one-time setup; it then runs daily by itself):
   ```
   sudo apt install -y unattended-upgrades
   sudo dpkg-reconfigure -plow unattended-upgrades   # answer Yes
   ```
   It does not reboot for you. Reboot by hand now and then (`sudo reboot`).
5. **Install Docker Engine** from Docker's own repo, following https://docs.docker.com/engine/install/debian/ ("Install using the apt repository"). Check: `sudo docker run hello-world`.
   Why not `apt install docker.io`: Debian's package is older and lacks the `docker compose` plugin.
6. **Create the `deploy` user** and let it run Docker:
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
7. **Lock down SSH.** In `/etc/ssh/sshd_config` set:
   ```
   PasswordAuthentication no
   PermitRootLogin no
   ```
   Then `sudo systemctl restart ssh`. **Keep your current session open** and test `ssh deploy@<server IP>` in a new terminal before closing it.
   Why: bots try passwords on every public server all day.
8. **Firewall** (allow 22 first, or you lock yourself out):
   ```
   sudo apt install -y ufw
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```
   80 and 443 are for Caddy (80 is also how Let's Encrypt checks the domain before giving a certificate).
9. **Swap (4 GB):**
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

- [ ] `ssh deploy@<server IP>` works with your key; password login and root login are refused
- [ ] `docker ps` works as `deploy` without `sudo`
- [ ] `sudo ufw status` shows only 22, 80, 443 allowed
- [ ] `free -h` shows swap
- [ ] Unattended-upgrades is enabled
- [ ] Server IP written down (needed by issue 33)

## Blocked by

None
