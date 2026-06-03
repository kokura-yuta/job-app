from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3

app = FastAPI()
companies = []

conn = sqlite3.connect("job_app.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT,
    mypage_url TEXT,
    login_id TEXT,
    password TEXT,
    es_text TEXT,
    deadline TEXT,
    event_date TEXT,
    result TEXT,
    memo TEXT,
    genre TEXT,
    priority TEXT)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")
try:
    cursor.execute("ALTER TABLE companies ADD COLUMN genre TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE companies ADD COLUMN priority TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE companies ADD COLUMN user_id INTEGER")
except sqlite3.OperationalError:
    pass


conn.commit()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request, user_id: int):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"user_id": user_id}
    )

@app.post("/add")
def add_company(
    company_name: str = Form(""),
    mypage_url: str = Form(""),
    login_id: str = Form(""),
    password: str =Form(""),
    es_text: str = Form(""),
    deadline: str = Form(""),
    event_date: str = Form(""),
    result: str = Form("未定"),
    memo: str = Form(""),
    genre: str = Form(""),
    priority: str = Form(""),
    user_id: int = Form(...)

):
    cursor.execute("""
    INSERT INTO companies (
        company_name,
        mypage_url,
        login_id,
        password,
        es_text,
        deadline,
        event_date,
        result,
        memo,
        genre,
        priority,
        user_id
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    company_name,
        mypage_url,
        login_id,
        password,
        es_text,
        deadline,
        event_date,
        result,
        memo,
        genre,
        priority,
        user_id

))

    conn.commit()

    return RedirectResponse(
            url=f"/list?user_id={user_id}",
            status_code=303
    )
@app.get("/list", response_class=HTMLResponse)
def show_list(request: Request, user_id: int, keyword: str = Query("")):
    if keyword:
        cursor.execute(
            """
            SELECT * FROM companies 
            WHERE user_id = ?
            AND company_name LIKE ?
            ORDER BY deadline ASC
            """,
            (user_id, f"%{keyword}%",)
        )
    else:
        cursor.execute(
            """
            SELECT * FROM companies 
            WHERE user_id = ?
            ORDER BY deadline ASC
            """,
            (user_id,)
        )
    rows = cursor.fetchall()
    print(rows)

    companies = []
    for row in rows:
        company = {
            "id": row[0],
            "company_name":row[1],
            "mypage_url":row[2],
            "login_id":row[3],
            "password":row[4],
            "es_text":row[5],
            "deadline":row[6],
            "event_date":row[7],
            "result":row[8],
            "memo":row[9],
            "genre":row[10],
            "priority":row[11]

        }

        companies.append(company)
    
    grouped_companies = {}

    for company in companies:
        genre = company.get("genre") or "未設定"
        if genre not in grouped_companies:
            grouped_companies[genre] = []
        grouped_companies[genre].append(company)

    return templates.TemplateResponse(
        request=request,
        name="list.html",
        context={"companies": companies,
                 "grouped_companies": grouped_companies,
                 "user_id": user_id}
)

@app.post("/delete/{id}")
def delete_company(id: int):
    cursor.execute("DELETE FROM companies WHERE id = ?", (id,))
    conn.commit()

    return RedirectResponse(
        url=f"/list?user_id={user[0]}",
        status_code=303
    )

@app.get("/edit/{id}")
def edit_company(id: int, request: Request, user_id: int):

    cursor.execute(
        "SELECT * FROM companies WHERE id = ?", 
        (id,)
    )
    row = cursor.fetchone()
    
    if row is None:
        return RedirectResponse(
            url=f"/list?user_id={user_id}",
            status_code=303
        )

    company = {
        "id": row[0],
        "company_name":row[1],
        "mypage_url":row[2],
        "login_id":row[3],
        "password":row[4],
        "es_text":row[5],
        "deadline":row[6],
        "event_date":row[7],
        "result":row[8],
        "memo":row[9],
        "genre":row[10],
        "priority":row[11],
        "user_id":row[12]

    }

    return templates.TemplateResponse(
        request=request,
        name="edit.html",
        context={"company": company,
        "user_id": user_id}
    )




@app.post("/update/{id}")
def update_company(
    id: int,
    company_name: str = Form(""),
    mypage_url: str = Form(""),
    login_id: str = Form(""),
    password: str = Form(""),
    es_text: str = Form(""),
    deadline: str = Form(""),
    event_date: str = Form(""),
    result: str = Form(""),
    memo: str = Form(""),
    genre: str = Form(""),
    priority: str = Form(""),
    user_id: int = Form("")
):
    cursor.execute("""
    UPDATE companies
    SET
        company_name = ?,
        mypage_url = ?,
        login_id = ?,
        password = ?,
        es_text = ?,
        deadline = ?,
        event_date = ?,
        result = ?,
        memo = ?,
        genre = ?,
        priority = ?
    WHERE id = ? AND user_id = ?
    """, (
        company_name,
        mypage_url,
        login_id,
        password,
        es_text,
        deadline,
        event_date,
        result,
        memo,
        genre,
        priority,
        id,
        user_id
    ))

    conn.commit()

    return RedirectResponse(
        url=f"/list?user_id={user_id}",
        status_code=303
    )
@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )

@app.post("/register")
def register_user(
    username: str = Form(...),
    password: str = Form(...)
):
    conn = sqlite3.connect("job_app.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
        """
        INSERT INTO users (username, password)
        VALUES (?,?)
        """,
        (username, password)
     )

        conn.commit()

    except sqlite3.IntegrityError:
      return HTMLResponse("このユーザー名はすでに使われています")

    return RedirectResponse(
        url="/login",
        status_code=303
)

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )
@app.post("/login")
def login_user(
    username: str = Form(...),
    password: str = Form(...)
):
    conn = sqlite3.connect("job_app.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM users
        WHERE username = ? AND password = ?
        """,
        (username, password)
    )

    user = cursor.fetchone()

    if user:
        return RedirectResponse(
            url=f"/list?user_id={user[0]}",
            status_code=303
        )
    else:
        return RedirectResponse(
            url="/login",
            status_code=303
        )
@app.get("/logout")
def logout():
    return RedirectResponse(
        url="/login",
        status_code=303
    )



