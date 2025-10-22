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

Run (with .env)
```bash
docker run --rm -it -p 8000:8000 --env-file .env be1-api:0.1.2
```

Endpoints

Swagger: http://127.0.0.1:8000/docs

Health: GET /healthz

CORS

Set allowed origins via .env:
```bash
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```