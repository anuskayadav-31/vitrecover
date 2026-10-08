VITRecover
WEB-01 — VIT Campus Lost & Found Recovery Portal

Features
- Lost/found reporting
- VIT campus locations and categories
- Student registration/login
- Private claim verification
- Claim approval/rejection
- Private recovery messaging
- Resolved-item lifecycle
- Search and filtering

Tech Stack
- FastAPI
- Jinja2
- SQLite
- HTML/CSS

Local Setup
1. python -m venv .venv
2. .venv\Scripts\activate
3. pip install -r requirements.txt
4. uvicorn app.main:app --reload
5. Open http://127.0.0.1:8000

Database
The SQLite database is created automatically by the application on first run.
The local database file is excluded from Git using .gitignore.

Main Workflow
Report → Browse → Claim → Private verification → Approve/Reject
→ Private conversation → Resolve

Privacy
Public listings do not expose claimant verification answers or
private recovery conversations.

Repository Structure
app/main.py
templates/
static/
requirements.txt
README.md