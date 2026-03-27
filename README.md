# ProgramPigeon

A fitness coaching platform for coaches to deliver workout plans and communicate with clients.

---

## Local Development

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### First-time setup

1. **Create your environment file**

   ```bash
   cp backend/.env.example backend/.env
   ```

   Open `backend/.env` and set a real `SECRET_KEY` (any long random string). The default database credentials work as-is.

2. **Start all containers**

   ```bash
   docker-compose up --build
   ```

3. **Confirm all containers are running** (in a second terminal)

   ```bash
   docker ps
   ```

   You should see all three containers up and the `db` marked as `(healthy)`:

   ```
   CONTAINER ID   IMAGE                   COMMAND                  STATUS
   xxxxxxxxxxxx   node:20-alpine          "docker-entrypoint.s…"   Up X minutes          programpigeon-frontend-1
   xxxxxxxxxxxx   programpigeon-backend   "uvicorn app.main:ap…"   Up X minutes          programpigeon-backend-1
   xxxxxxxxxxxx   postgres:16-alpine      "docker-entrypoint.s…"   Up X minutes (healthy) programpigeon-db-1
   ```

   Database tables are created automatically when the backend starts — no extra steps needed.

### Starting up (after first-time setup)

```bash
docker-compose up
```

### Taking down the deployment

```bash
docker-compose down
```

You should see all containers stop:

```
[+] Running 3/3
 ✔ Container programpigeon-frontend-1  Removed
 ✔ Container programpigeon-backend-1   Removed
 ✔ Container programpigeon-db-1        Removed
```

To also wipe the database (full reset):

```bash
docker-compose down -v
```

---

## Service URLs

| Service       | URL                          |
|---------------|------------------------------|
| Frontend      | http://localhost:3000        |
| Backend API   | http://localhost:8000        |
| API Docs      | http://localhost:8000/docs   |
| Register      | http://localhost:3000/register |

---

## Useful commands

| Command | Purpose |
|---------|---------|
| `docker ps` | Check which containers are running |
| `docker-compose logs backend` | View backend logs |
| `docker-compose up -d --force-recreate backend` | Restart backend and reload `.env` changes |
| `docker-compose exec backend alembic upgrade head` | Apply pending DB migrations |
