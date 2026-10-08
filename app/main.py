from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import hashlib, os, hmac
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "vitrecover.db"
app = FastAPI(title="VITRecover")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")
LOCATIONS = [
    "SJT",
    "TT",
    "PRP",
    "SMV",
    "MB",
    "GDN",
    "CDMM",
    "LH-A",
    "LH-B",
    "LH-C",
    "LH-D",
    "LH-E",
    "LH-F",
    "LH-G",
    "LH-H",
    "LH-I",
    "LH-J",
    "MH-A",
    "MH-B",
    "MH-C",
    "MH-D",
    "MH-E",
    "MH-F",
    "MH-G",
    "MH-H",
    "MH-I",
    "MH-J",
    "MH-K",
    "MH-L",
    "MH-M",
    "MH-N",
    "MH-O",
    "MH-P",
    "MH-Q",
    "MH-R",
    "MH-S",
    "MH-T",
    "Gazebo",
    "Food Mall",
    "DC",
    "Central Library",
    "Sports Complex",
]
CATEGORIES = [
    "ID Cards",
    "Room Keys",
    "Calculators",
    "Lab Equipment",
    "Earphones",
    "Wallets",
]


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return salt.hex() + ":" + digest.hex()


def verify_password(password, stored):
    salt_hex, digest_hex = stored.split(":", 1)
    digest = hashlib.scrypt(
        password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.executescript(
        """CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, regno TEXT UNIQUE, email TEXT UNIQUE, name TEXT, password TEXT);
    CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY, owner_id INTEGER, kind TEXT, title TEXT, description TEXT, location TEXT, category TEXT, challenge TEXT, answer TEXT, status TEXT DEFAULT 'ACTIVE');
    CREATE TABLE IF NOT EXISTS claims(id INTEGER PRIMARY KEY, item_id INTEGER, claimant_id INTEGER, response TEXT, status TEXT DEFAULT 'PENDING');
    CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, claim_id INTEGER, sender_id INTEGER, body TEXT);
    """
    )
    return con


@app.on_event("startup")
def init():
    db().close()


def current_user(request):
    return request.cookies.get("user_id")


def user(id):
    if not id:
        return None
    con = db()
    u = con.execute("SELECT * FROM users WHERE id=?", (id,)).fetchone()
    con.close()
    return u


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    con = db()
    items = con.execute(
        "SELECT * FROM items WHERE status IN ('ACTIVE', 'CLAIM_APPROVED') ORDER BY id DESC"
    ).fetchall()
    con.close()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "items": items,
            "user": user(current_user(request)),
            "locations": LOCATIONS,
            "categories": CATEGORIES,
        },
    )


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={},
    )


@app.post("/register")
def register(
    regno: str = Form(...),
    email: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
):
    if "@" not in email or len(password) < 6:
        raise HTTPException(
            400, "Use a valid email and a password of at least 6 characters."
        )
    con = db()
    try:
        con.execute(
            "INSERT INTO users(regno,email,name,password) VALUES(?,?,?,?)",
            (
                regno.strip(),
                email.lower().strip(),
                name.strip(),
                hash_password(password),
            ),
        )
        con.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Registration number or email already exists.")
    con.close()
    return RedirectResponse("/login", 303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )


@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    con = db()
    u = con.execute(
        "SELECT * FROM users WHERE email=?", (email.lower().strip(),)
    ).fetchone()
    con.close()
    if not u or not verify_password(password, u["password"]):
        raise HTTPException(401, "Invalid credentials")
    r = RedirectResponse("/", 303)
    r.set_cookie("user_id", str(u["id"]), httponly=True, samesite="lax")
    return r


@app.get("/logout")
def logout():
    r = RedirectResponse("/", 303)
    r.delete_cookie("user_id")
    return r


@app.post("/items")
def create_item(
    request: Request,
    kind: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    category: str = Form(...),
    challenge: str = Form(...),
    answer: str = Form(...),
):
    u = current_user(request)
    if not u:
        raise HTTPException(401, "Login required")
    if (
        location not in LOCATIONS
        or category not in CATEGORIES
        or kind not in ["LOST", "FOUND"]
    ):
        raise HTTPException(400, "Invalid listing data")
    con = db()
    con.execute(
        "INSERT INTO items(owner_id,kind,title,description,location,category,challenge,answer) VALUES(?,?,?,?,?,?,?,?)",
        (
            u,
            kind,
            title,
            description,
            location,
            category,
            challenge,
            answer.lower().strip(),
        ),
    )
    con.commit()
    con.close()
    return RedirectResponse("/", 303)


@app.post("/claim/{item_id}")
def claim(request: Request, item_id: int, response: str = Form(...)):
    u = current_user(request)
    if not u:
        raise HTTPException(401, "Login required")
    con = db()
    item = con.execute(
        "SELECT * FROM items WHERE id=? AND status='ACTIVE'", (item_id,)
    ).fetchone()
    if not item or item["owner_id"] == int(u):
        raise HTTPException(400, "Invalid claim")
    con.execute(
        "INSERT INTO claims(item_id,claimant_id,response) VALUES(?,?,?)",
        (item_id, u, response.strip()),
    )
    con.commit()
    con.close()
    return RedirectResponse("/", 303)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    u = current_user(request)
    if not u:
        return RedirectResponse("/login", 303)
    con = db()
    claims = con.execute(
        "SELECT c.*,i.title,i.challenge,i.answer,i.owner_id FROM claims c JOIN items i ON i.id=c.item_id WHERE i.owner_id=? ORDER BY c.id DESC",
        (u,),
    ).fetchall()
    approved_claims = con.execute(
        """
    SELECT
        c.*,
        i.title,
        i.owner_id
    FROM claims c
    JOIN items i ON i.id = c.item_id
    WHERE c.claimant_id = ?
      AND c.status = 'APPROVED'
    ORDER BY c.id DESC
    """,
        (u,),
    ).fetchall()
    own = con.execute(
        "SELECT * FROM items WHERE owner_id=? ORDER BY id DESC", (u,)
    ).fetchall()
    con.close()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "claims": claims,
            "approved_claims": approved_claims,
            "own": own,
            "user": user(u),
        },
    )


@app.post("/claims/{claim_id}/{decision}")
def decide(request: Request, claim_id: int, decision: str):
    u = current_user(request)
    if not u or decision not in ["APPROVED", "REJECTED"]:
        raise HTTPException(400, "Invalid request")
    con = db()
    claim = con.execute(
        "SELECT c.*,i.owner_id,i.id item_id FROM claims c JOIN items i ON i.id=c.item_id WHERE c.id=?",
        (claim_id,),
    ).fetchone()
    if not claim or claim["owner_id"] != int(u):
        raise HTTPException(403, "Only the finder can decide")
    con.execute("UPDATE claims SET status=? WHERE id=?", (decision, claim_id))
    if decision == "APPROVED":
        con.execute(
            "UPDATE items SET status='CLAIM_APPROVED' WHERE id=?", (claim["item_id"],)
        )
    con.commit()
    con.close()
    return RedirectResponse("/dashboard", 303)


@app.post("/resolve/{item_id}")
def resolve(request: Request, item_id: int):
    u = current_user(request)
    if not u:
        raise HTTPException(401, "Login required")
    con = db()
    item = con.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    if not item:
        raise HTTPException(404, "Item not found")
    # Owner can resolve; approved claimant can also resolve.
    approved = con.execute(
        "SELECT 1 FROM claims WHERE item_id=? AND claimant_id=? AND status='APPROVED'",
        (item_id, u),
    ).fetchone()
    if item["owner_id"] != int(u) and not approved:
        raise HTTPException(403, "Not authorized")
    con.execute("UPDATE items SET status='RESOLVED' WHERE id=?", (item_id,))
    con.commit()
    con.close()
    return RedirectResponse("/dashboard", 303)


@app.get("/messages/{claim_id}", response_class=HTMLResponse)
def messages_page(request: Request, claim_id: int):
    current = current_user(request)
    if not current:
        return RedirectResponse("/login", 303)

    current_id = int(current)
    con = db()

    claim = con.execute(
        """
        SELECT
            c.id,
            c.item_id,
            c.claimant_id,
            c.status,
            i.title,
            i.owner_id
        FROM claims c
        JOIN items i ON i.id = c.item_id
        WHERE c.id = ?
        """,
        (claim_id,),
    ).fetchone()

    if not claim:
        con.close()
        raise HTTPException(404, "Claim not found")

    # Only the finder/owner or the approved claimant can access
    # the private conversation.
    if claim["status"] != "APPROVED":
        con.close()
        raise HTTPException(403, "Messaging is available only after claim approval")

    if current_id not in (claim["owner_id"], claim["claimant_id"]):
        con.close()
        raise HTTPException(403, "You are not part of this conversation")

    messages = con.execute(
        """
        SELECT id, sender_id, body
        FROM messages
        WHERE claim_id = ?
        ORDER BY id ASC
        """,
        (claim_id,),
    ).fetchall()

    con.close()

    return templates.TemplateResponse(
        request=request,
        name="messages.html",
        context={
            "claim": claim,
            "messages": messages,
            "current_user_id": current_id,
            "user": user(current_id),
        },
    )


@app.post("/messages/{claim_id}")
def send_message(
    request: Request,
    claim_id: int,
    body: str = Form(...),
):
    current = current_user(request)
    if not current:
        return RedirectResponse("/login", 303)

    current_id = int(current)
    body = body.strip()

    if not body:
        raise HTTPException(400, "Message cannot be empty")

    if len(body) > 2000:
        raise HTTPException(400, "Message is too long")

    con = db()

    claim = con.execute(
        """
        SELECT
            c.id,
            c.claimant_id,
            c.status,
            i.owner_id
        FROM claims c
        JOIN items i ON i.id = c.item_id
        WHERE c.id = ?
        """,
        (claim_id,),
    ).fetchone()

    if not claim:
        con.close()
        raise HTTPException(404, "Claim not found")

    if claim["status"] != "APPROVED":
        con.close()
        raise HTTPException(403, "Messaging is available only after approval")

    if current_id not in (claim["owner_id"], claim["claimant_id"]):
        con.close()
        raise HTTPException(403, "You are not part of this conversation")

    con.execute(
        """
        INSERT INTO messages(claim_id, sender_id, body)
        VALUES (?, ?, ?)
        """,
        (claim_id, current_id, body),
    )

    con.commit()
    con.close()

    return RedirectResponse(f"/messages/{claim_id}", 303)
