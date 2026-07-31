# Deploy Study Mind on a DigitalOcean Droplet

This Docker setup runs the Next.js frontend, FastAPI backend, and Caddy reverse
proxy on one Droplet. Caddy provides HTTPS automatically when `DOMAIN` is a
real domain pointing at the Droplet.

## 1. Create the Droplet

Choose **Ubuntu 24.04 (x64)** under the **OS** tab. Do not choose the Docker
Marketplace image. Use at least the 2 GB RAM plan for a reliable deployment;
the 1 GB plan is suitable only for light personal testing. Add your SSH key and
enable DigitalOcean monitoring. In Networking, allow inbound TCP ports 22, 80,
and 443 only.

Create an `A` DNS record for your domain that points to the Droplet IPv4
address before starting the containers. Caddy needs this to issue HTTPS.

## 2. Set up the server

Connect as root, then run:

```bash
apt update && apt upgrade -y
apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sh
apt install -y docker-compose-plugin
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

For the 1 GB Droplet, add 2 GB swap before the first image build:

```bash
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

## 3. Copy the project and add secrets

```bash
git clone YOUR_REPOSITORY_URL study-mind-ai
cd study-mind-ai
cp .env.example .env
cp backend/.env.example backend/.env
nano .env
nano backend/.env
```

The root `.env` needs `DOMAIN`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, and
`CLERK_SECRET_KEY`. The backend `.env` needs `GEMINI_API_KEY` and
`CLERK_JWT_ISSUER`. Never commit either file.

Each signed-in user's collections are stored under a namespace derived from
their verified Clerk user ID. Users can access only their own collections.
The API allows up to 10 quiz generations and 50 Ask requests per user per UTC
day; each quiz can contain at most 10 questions. Existing collections created
before namespacing are left untouched and will not appear in user accounts;
back up the data volume before deployment if you need to migrate old content.

For a quick HTTP-only test by IP address, set `DOMAIN=:80`; change it to your
domain and restart after DNS is configured.

## 4. Build and start

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f --tail=100
```

The first build downloads Python packages and the embedding model, so it can
take several minutes. Open `https://your-domain` after all services are up.

## Updates and backups

```bash
git pull
docker compose up -d --build
docker image prune -f
```

Study documents, Chroma vectors, and SQLite data live in the Docker volume
named `study-mind-data`. Back it up before destroying the Droplet:

```bash
docker run --rm -v study-mind-ai_study-mind-data:/data -v "$PWD":/backup \
  alpine tar czf /backup/study-mind-data-backup.tgz -C /data .
```
