# VITRecover

WEB-01 — VIT Campus Lost & Found Recovery Portal.

A FastAPI + Jinja2 + SQLite MVP with a polished VITRecover interface, public lost/found board, private ownership verification, authenticated claims, finder approval, private messaging, and recovery resolution.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.
