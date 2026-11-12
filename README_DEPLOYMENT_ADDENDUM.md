# Fresh VPS deployment (Ubuntu 22.04+)

The supported deployment path is Docker Compose. Python 3.12 is used in the image;
Python 3.10 is end-of-life and should not be used for a new installation.

## 1. Prepare configuration

```bash
cp .env.example .env
nano .env
```

Set `BOT_TOKEN`, `API_ID`, `API_HASH`, and `OWNER_ID`. Keep `.env` private:
do not commit it or paste its values into support chats.

## 2. Build and start

```bash
docker compose build --pull
docker compose up -d
docker compose ps
docker compose logs --tail=100 -f fzbypass
```

The bot starts automatically after a VPS reboot. Logs and restart-notification
state are persisted in the local `data/` directory. The health endpoint listens
inside the container on port 8080; it does not need to be exposed publicly.

## 3. Update safely

```bash
git pull --ff-only
docker compose build --pull
docker compose up -d
```

Do not run `update.py` inside the running container. The runtime no longer
self-updates or deletes its Git metadata. The owner `/restart` command only
restarts the bot process; use Compose to deploy code changes.

## 4. Useful operations

```bash
docker compose ps
docker compose logs --tail=200 fzbypass
docker compose restart fzbypass
docker compose down
```

`docker compose down` stops the bot but preserves `data/` and `.env`.
Do not use `docker compose down -v` unless you intentionally want to remove
named volumes (this stack does not require any).

## Resource profile

The Compose service is capped at 1.5 CPU and 2 GiB RAM, leaving resources for
Ubuntu and other VPS tasks. Adjust only if monitoring shows the bot needs more.
