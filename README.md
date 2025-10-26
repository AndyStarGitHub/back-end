# 🧩 Meduzzen BE-1 Project

This project is a minimal FastAPI application following clean structure, 
environment separation, and standard GitHub workflow conventions.

---

## 🚀 Features

- **FastAPI** — modern, async, type-safe web framework  
- **Pydantic Settings** — environment-based configuration with `.env` support  
- **Uvicorn** — ASGI server for local and production use  
- **pytest + httpx** — async test setup  
- **Black / Flake8** — formatting & linting tools  

---

## 🧱 Project Structure



.
├─ app/
│ ├─ init.py
│ ├─ main.py # Uvicorn entrypoint
│ └─ core/
│ ├─ init.py
│ └─ config.py # Pydantic settings loader
│ ├─ init.py
│ └─ db/
│ ├─ init.py
│ └─ routers/
│ ├─ init.py
│ └─ schemas/
│ ├─ init.py
│ └─ services/
│ ├─ init.py
│ └─ utils/
├─ tests/
│ └─ test_healthz.py # Example tests
├─ .env # Local environment variables (not committed)
├─ .env.sample # Example env file
├─ pytest.ini
├─ .gitignore
└─ README.md


---

## ⚙️ Environment Setup

### 1️⃣ Clone the repository
```bash
git clone https://github.com/AndyStarGitHub/back-end
cd be-1
```

2️⃣ Create and activate virtual environment

Windows (PowerShell):

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
```

3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

4️⃣ Configure environment variables

Create a .env file in the project root (use .env.sample as a reference):
```bash
APP_NAME=FastAPI Best Practice
ENV=dev
DEBUG=True
LOG_LEVEL=DEBUG
SECRET_KEY=change_me_locally
```
▶️ Running the Application

Run the FastAPI app locally:
```bash
uvicorn app.main:app --reload
```

Health check: http://127.0.0.1:8000

Example response:

{
  "status_code": 200,
  "detail": "ok",
  "result": "working"
}

🧪 Running Tests
```
pytest -q
```

## 🐳 Run with Docker

### Build
```bash
docker build -t be1-api:0.1.2 .
```

### Run (with .env)
```bash
docker run --rm -it -p 8000:8000 --env-file .env be1-api:0.1.2
```

### Endpoints

Swagger: http://127.0.0.1:8000/docs

Health: GET /healthz

### CORS

Set allowed origins via .env:
```bash
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 🐳 Run the Application with Docker Compose

This project uses Docker Compose to run the FastAPI application together with PostgreSQL and Redis.

🧩 Services Overview
Service	Description	Port
api	FastAPI backend (main application)	8000
db	PostgreSQL database	5432 (internal)
redis	Redis in-memory data store	6379 (internal)
⚙️ Environment Variables

Make sure your .env file contains the following values:

APP_NAME=FastAPI Best Practice

# CORS (Frontend URLs)
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# PostgreSQL
POSTGRES_DB=appdb
POSTGRES_USER=appuser
POSTGRES_PASSWORD=apppass
DATABASE_URL=postgresql+asyncpg://appuser:apppass@db:5432/appdb

# Redis
REDIS_URL=redis://redis:6379/0

# App runtime
HOST=0.0.0.0
PORT=8000
RELOAD=false


🔐 Never commit your real .env file.
Instead, update .env.sample for reference.

🚀 Run the Stack

Build and start all services:
```bash
docker compose up --build
```

Run in the background (detached mode):
```bash
docker compose up -d --build
```

Stop all containers:
```bash
docker compose down
```

Rebuild without cache (e.g. after start.sh or dependency changes):
```bash
docker compose build --no-cache
```

✅ Health Checks

Once the containers are running:

Endpoint	Description	Example Response
GET /	Base healthcheck	{"status_code":200,"detail":"ok","result":"working"}
GET /ping/db	PostgreSQL connectivity	{"postgres_ok":true}
GET /ping/redis	Redis connectivity	{"redis_ok":true}

Swagger UI → http://127.0.0.1:8000/docs

🧠 Notes

Code changes in the app directory trigger auto-reload inside the container (thanks to the volumes mount).

If port 5432 or 8000 is already used on your host, change the left side in docker-compose.yml, for example:

ports:
  - "8001:8000"
  - "5433:5432"


Redis is currently used only for connectivity tests, but will later serve as a cache, session store, or task queue backend.

# Database Migrations Setup

## 1. Environment Setup

Add your database connection string to the `.env` file (with real user and password):
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/mydb
```

> Use `host=db` when running inside Docker, or `host=localhost` for local development.

---

## 2. Initialize Alembic

If migrations are not yet initialized, run:
```bash
docker compose run --rm --entrypoint "" api alembic init -t async migrations
```
---

## 3. Configure Alembic

Edit `migrations/env.py` to ensure the following:
- Import your SQLAlchemy `Base` and model modules:
- Load the database URL from environment variables (`os.getenv("DATABASE_URL")`).
- Keep `compare_type=True` to detect column type changes.
---

## 4. Generate Migrations

To generate a new migration automatically based on your models:
```bash
docker compose run --rm --entrypoint "" api alembic revision --autogenerate -m "create users table"
```
---

## 5. Apply Migrations

To apply all pending migrations to the database:
```bash
docker compose run --rm --entrypoint "" api alembic upgrade head
```
---
